"""
WebDAV Service for Yandex.Disk file storage operations

Provides WebDAV client functionality for uploading files to Yandex.Disk.
Supports both Basic Auth (username:password) and OAuth token authentication.

For OAuth tokens, uses Yandex.Disk REST API for fast uploads.

Requirements: 2.1, 2.2, 2.3, 2.5, 2.6, 9.2, 11.3, 11.4
"""

import re
import os
import logging
import urllib.parse
from dataclasses import dataclass
from typing import Optional, Callable
import httpx
import asyncio
import aiofiles

logger = logging.getLogger(__name__)

YANDEX_DISK_API_BASE = "https://cloud-api.yandex.net/v1/disk"
UPLOAD_CHUNK_SIZE = 1024 * 1024
CONNECT_TIMEOUT = 30.0
READ_TIMEOUT = 600.0
WRITE_TIMEOUT = 600.0
POOL_TIMEOUT = 30.0


@dataclass
class StorageInfo:
    """Storage information"""
    total_space: int
    used_space: int
    free_space: int
    is_connected: bool


class _AsyncProgressReader:
    """Asynchronous iterator for streaming upload with progress tracking.
    
    httpx.AsyncClient requires an async iterable for streaming content.
    Using a sync iterator causes RuntimeError.
    """

    def __init__(self, file_path: str, total_size: int, chunk_size: int = UPLOAD_CHUNK_SIZE,
                 progress_callback: Optional[Callable[[int, int], None]] = None):
        self._file_path = file_path
        self._total_size = total_size
        self._chunk_size = chunk_size
        self._progress_callback = progress_callback
        self._bytes_sent = 0

    def __aiter__(self):
        return self._stream()

    async def _stream(self):
        async with aiofiles.open(self._file_path, "rb") as f:
            while True:
                chunk = await f.read(self._chunk_size)
                if not chunk:
                    break
                self._bytes_sent += len(chunk)
                if self._progress_callback:
                    try:
                        self._progress_callback(self._bytes_sent, self._total_size)
                    except Exception:
                        pass
                yield chunk


class WebDAVService:
    """WebDAV service for Yandex.Disk file storage operations"""

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        self._config: Optional["WebDAVConfig"] = None
        self._auth_header: Optional[dict] = None
        self._is_oauth: bool = False

    async def connect(self, config: "WebDAVConfig") -> bool:
        """Connect to Yandex.Disk WebDAV storage"""
        from bot.database import WebDAVConfig

        if self._client is not None:
            await self.disconnect()

        try:
            # Check if password is OAuth token (y0_, y1_, y2_, y3_, t1., AQAA)
            self._is_oauth = config.password.startswith(("y0_", "y1_", "y2_", "y3_", "t1.", "AQAA"))

            if self._is_oauth:
                self._auth_header = {"Authorization": f"OAuth {config.password}"}
                auth = None
                logger.info("Detected OAuth token, will use REST API for uploads")
            else:
                self._auth_header = {}
                auth = (config.username, config.password)
                logger.info("Detected app password, will use WebDAV for uploads")

            self._client = httpx.AsyncClient(
                auth=auth,
                timeout=httpx.Timeout(
                    connect=CONNECT_TIMEOUT,
                    read=READ_TIMEOUT,
                    write=WRITE_TIMEOUT,
                    pool=POOL_TIMEOUT
                ),
                follow_redirects=True,
            )

            self._config = config
            connection_ok = await self.test_connection()

            if not connection_ok:
                await self.disconnect()

            return connection_ok

        except Exception as e:
            self._client = None
            self._config = None
            self._auth_header = None
            raise ConnectionError(f"Failed to connect to Yandex.Disk WebDAV: {e}")
            self._config = None
            self._auth_header = None
            raise ConnectionError(f"Failed to connect to Yandex.Disk WebDAV: {e}")

    async def disconnect(self) -> None:
        """Disconnect from Yandex.Disk WebDAV storage"""
        if self._client:
            await self._client.aclose()
            self._client = None
        self._config = None
        self._auth_header = None

    async def test_connection(self) -> bool:
        """Test Yandex.Disk connection"""
        if self._client is None:
            return False

        if self._is_oauth:
            try:
                resp = await self._client.get(f"{YANDEX_DISK_API_BASE}/", headers=self._auth_header)
                if resp.status_code == 200:
                    return True
            except Exception:
                pass

        try:
            response = await self._client.request("PROPFIND", self._config.url,
                                                 headers={**self._auth_header, "Depth": "0"})
            return response.status_code in (200, 207)
        except Exception:
            return False

    async def get_storage_info(self) -> StorageInfo:
        """Get storage information from Yandex.Disk"""
        if self._client is None:
            return StorageInfo(0, 0, 0, is_connected=False)

        if self._is_oauth:
            try:
                resp = await self._client.get(f"{YANDEX_DISK_API_BASE}/", headers=self._auth_header)
                if resp.status_code == 200:
                    data = resp.json()
                    total = data.get("total_space", 0)
                    used = data.get("used_space", 0)
                    return StorageInfo(total, used, total - used, is_connected=True)
            except Exception:
                pass

        try:
            response = await self._client.request(
                "PROPFIND", self._config.url,
                headers={**self._auth_header, "Depth": "0"},
                content='<?xml version="1.0"?><D:propfind xmlns:D="DAV:"><D:prop>'
                       '<D:quota-available-bytes/><D:quota-used-bytes/></D:prop></D:propfind>'
            )

            if response.status_code in (200, 207):
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.text)
                ns = {"D": "DAV:"}
                avail = root.find(".//D:quota-available-bytes", ns)
                used = root.find(".//D:quota-used-bytes", ns)
                free_space = int(avail.text) if avail is not None and avail.text else 0
                used_space = int(used.text) if used is not None and used.text else 0
                return StorageInfo(free_space + used_space, used_space, free_space, is_connected=True)
        except Exception:
            pass

        return StorageInfo(0, 0, 0, is_connected=await self.test_connection())

    async def upload_file(self, local_path: str, remote_path: str,
                         progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        """Upload file to Yandex.Disk"""
        if self._client is None:
            raise ConnectionError("Not connected to Yandex.Disk WebDAV")

        file_size = os.path.getsize(local_path)
        logger.info("Uploading %s (%.1f MB) → %s", local_path, file_size / 1024 / 1024, remote_path)
        logger.info("OAuth mode: %s, Password prefix: %s", self._is_oauth, 
                   self._config.password[:4] if self._config and self._config.password else "None")

        remote_dir = "/".join(remote_path.split("/")[:-1])
        if remote_dir:
            try:
                await self.create_directory(remote_dir)
            except Exception as exc:
                logger.warning("create_directory failed: %s", exc)

        if self._is_oauth:
            try:
                logger.info("Using REST API for upload (OAuth detected)")
                return await self._upload_via_rest_api(local_path, remote_path, file_size, progress_callback)
            except Exception as exc:
                logger.warning("REST API upload failed (%s), falling back to WebDAV", exc)
        else:
            logger.info("Using WebDAV PUT for upload (Basic Auth)")

        return await self._upload_via_webdav(local_path, remote_path, file_size, progress_callback)

    async def _upload_via_rest_api(self, local_path: str, remote_path: str, file_size: int,
                                   progress_callback: Optional[Callable[[int, int], None]]) -> bool:
        """Upload via Yandex.Disk REST API"""
        api_path = f"disk:/{remote_path.lstrip('/')}" if not remote_path.startswith("disk:/") else remote_path

        resp = await self._client.get(f"{YANDEX_DISK_API_BASE}/resources/upload",
                                     params={"path": api_path, "overwrite": "true"},
                                     headers=self._auth_header)

        if resp.status_code == 409:
            await self._ensure_dirs_rest(api_path)
            resp = await self._client.get(f"{YANDEX_DISK_API_BASE}/resources/upload",
                                         params={"path": api_path, "overwrite": "true"},
                                         headers=self._auth_header)

        if resp.status_code != 200:
            raise IOError(f"Failed to get upload URL: {resp.status_code} {resp.text}")

        upload_url = resp.json().get("href")
        if not upload_url:
            raise IOError("No upload URL in REST API response")

        logger.info("Got REST API upload URL, starting streaming PUT (%d bytes)", file_size)

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=CONNECT_TIMEOUT,
                read=READ_TIMEOUT,
                write=WRITE_TIMEOUT,
                pool=POOL_TIMEOUT
            ),
            follow_redirects=True
        ) as upload_client:
            reader = _AsyncProgressReader(local_path, file_size, UPLOAD_CHUNK_SIZE, progress_callback)
            put_resp = await upload_client.put(upload_url, content=reader,
                                              headers={"Content-Length": str(file_size),
                                                      "Content-Type": "application/octet-stream"})

            logger.info("REST API upload response: %d", put_resp.status_code)

            if put_resp.status_code not in (200, 201, 202):
                raise IOError(f"REST API PUT failed: {put_resp.status_code} {put_resp.text}")

        if progress_callback:
            progress_callback(file_size, file_size)

        logger.info("Upload completed successfully via REST API")
        return True

    async def _ensure_dirs_rest(self, api_path: str) -> None:
        """Recursively create parent directories via REST API"""
        rel = api_path.replace("disk:/", "", 1)
        parts = rel.split("/")

        for i in range(1, len(parts)):
            dir_path = "disk:/" + "/".join(parts[:i])
            resp = await self._client.put(f"{YANDEX_DISK_API_BASE}/resources",
                                         params={"path": dir_path}, headers=self._auth_header)
            if resp.status_code not in (201, 409):
                logger.warning("mkdir REST %s → %d", dir_path, resp.status_code)

    async def _upload_via_webdav(self, local_path: str, remote_path: str, file_size: int,
                                progress_callback: Optional[Callable[[int, int], None]]) -> bool:
        """Upload via WebDAV PUT"""
        encoded_path = urllib.parse.quote(remote_path)
        full_url = f"{self._config.url.rstrip('/')}/{encoded_path.lstrip('/')}"

        logger.info("WebDAV streaming PUT to %s (%d bytes)", full_url, file_size)

        reader = _AsyncProgressReader(local_path, file_size, UPLOAD_CHUNK_SIZE, progress_callback)
        resp = await self._client.put(full_url, content=reader,
                                      headers={**self._auth_header, "Content-Length": str(file_size),
                                              "Content-Type": "application/octet-stream"})

        logger.info("WebDAV upload response: %d", resp.status_code)

        if resp.status_code not in (200, 201, 204):
            raise IOError(f"WebDAV upload failed: {resp.status_code} {resp.text}")

        if progress_callback:
            progress_callback(file_size, file_size)

        logger.info("Upload completed successfully via WebDAV PUT")
        return True

    async def create_directory(self, path: str) -> bool:
        """Create directory on Yandex.Disk"""
        if self._client is None:
            raise ConnectionError("Not connected to Yandex.Disk WebDAV")

        if self._is_oauth:
            try:
                api_path = f"disk:/{path.lstrip('/')}" if not path.startswith("disk:/") else path
                parts = api_path.replace("disk:/", "", 1).split("/")
                for i in range(1, len(parts) + 1):
                    dir_path = "disk:/" + "/".join(parts[:i])
                    resp = await self._client.put(f"{YANDEX_DISK_API_BASE}/resources",
                                                 params={"path": dir_path}, headers=self._auth_header)
                    if resp.status_code not in (201, 409):
                        logger.warning("mkdir REST %s → %d", dir_path, resp.status_code)
                return True
            except Exception:
                pass

        try:
            if await self.file_exists(path):
                return True
            response = await self._client.request("MKCOL",
                                                 f"{self._config.url.rstrip('/')}/{path.lstrip('/')}",
                                                 headers=self._auth_header)
            return response.status_code in (200, 201)
        except Exception:
            return False

    async def file_exists(self, path: str) -> bool:
        """Check if file or directory exists"""
        if self._client is None:
            raise ConnectionError("Not connected to Yandex.Disk WebDAV")

        if self._is_oauth:
            try:
                api_path = f"disk:/{path.lstrip('/')}" if not path.startswith("disk:/") else path
                resp = await self._client.get(f"{YANDEX_DISK_API_BASE}/resources",
                                             params={"path": api_path}, headers=self._auth_header)
                return resp.status_code == 200
            except Exception:
                pass

        try:
            response = await self._client.head(f"{self._config.url.rstrip('/')}/{path.lstrip('/')}",
                                              headers=self._auth_header)
            return response.status_code == 200
        except Exception:
            return False

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename by replacing invalid characters"""
        invalid_chars = r'[/\\:*?"<>|]'
        sanitized = re.sub(invalid_chars, "_", filename)
        sanitized = sanitized.strip(". ")
        return sanitized or "unnamed"