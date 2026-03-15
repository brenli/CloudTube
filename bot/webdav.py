"""
WebDAV Service for Yandex.Disk file storage operations

Uses Yandex.Disk REST API with OAuth token authentication.
Based on the working example with requests library.

Requirements: 2.1, 2.2, 2.3, 2.5, 2.6, 9.2, 11.3, 11.4
"""

import re
import os
import logging
from dataclasses import dataclass
from typing import Optional, Callable
import httpx
import aiofiles

logger = logging.getLogger(__name__)

YANDEX_DISK_API_BASE = "https://cloud-api.yandex.net/v1/disk"


@dataclass
class StorageInfo:
    """Storage information"""
    total_space: int
    used_space: int
    free_space: int
    is_connected: bool


class WebDAVService:
    """Yandex.Disk service for file storage operations"""

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        self._config: Optional["WebDAVConfig"] = None
        self._headers: dict = {}

    async def connect(self, config: "WebDAVConfig") -> bool:
        """Connect to Yandex.Disk using OAuth token"""
        from bot.database import WebDAVConfig

        if self._client is not None:
            await self.disconnect()

        try:
            self._config = config
            # Set OAuth header exactly like in the example
            self._headers = {"Authorization": f"OAuth {config.password}"}
            
            # Create HTTP client
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(connect=30.0, read=600.0, write=600.0, pool=30.0),
                follow_redirects=True
            )
            
            # Test connection by getting disk info
            is_valid = await self.test_connection()
            
            if not is_valid:
                await self.disconnect()
                logger.error("Invalid OAuth token")
                return False

            logger.info("Connected to Yandex.Disk successfully")
            return True

        except Exception as e:
            await self.disconnect()
            logger.error(f"Failed to connect: {e}")
            raise ConnectionError(f"Failed to connect to Yandex.Disk: {e}")

    async def disconnect(self) -> None:
        """Disconnect from Yandex.Disk"""
        if self._client:
            await self._client.aclose()
            self._client = None
        self._config = None
        self._headers = {}

    async def test_connection(self) -> bool:
        """Test Yandex.Disk connection"""
        if self._client is None:
            return False

        try:
            response = await self._client.get(
                f"{YANDEX_DISK_API_BASE}/",
                headers=self._headers
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    async def get_storage_info(self) -> StorageInfo:
        """Get storage information from Yandex.Disk"""
        if self._client is None:
            return StorageInfo(0, 0, 0, is_connected=False)

        try:
            response = await self._client.get(
                f"{YANDEX_DISK_API_BASE}/",
                headers=self._headers
            )
            
            if response.status_code == 200:
                data = response.json()
                total = data.get("total_space", 0)
                used = data.get("used_space", 0)
                return StorageInfo(total, used, total - used, is_connected=True)
            
            return StorageInfo(0, 0, 0, is_connected=False)
        except Exception as e:
            logger.error(f"Failed to get storage info: {e}")
            return StorageInfo(0, 0, 0, is_connected=False)

    async def _get_upload_url(self, disk_path: str, overwrite: bool = True) -> str:
        """Get upload URL from Yandex.Disk API (step 1) - exactly like in example"""
        url = f"{YANDEX_DISK_API_BASE}/resources/upload"
        params = {
            "path": disk_path,
            "overwrite": str(overwrite).lower()
        }
        
        response = await self._client.get(url, headers=self._headers, params=params)
        
        if response.status_code != 200:
            raise IOError(f"Failed to get upload URL: {response.status_code} {response.text}")
        
        return response.json()["href"]

    async def upload_file(self, local_path: str, remote_path: str,
                         progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        """Upload file to Yandex.Disk - exactly like in example"""
        if self._client is None:
            raise ConnectionError("Not connected to Yandex.Disk")

        if not os.path.exists(local_path):
            raise FileNotFoundError(f"File not found: {local_path}")

        file_size = os.path.getsize(local_path)
        logger.info("Uploading %s (%.1f MB) → %s", local_path, file_size / 1024 / 1024, remote_path)

        # Convert path to disk:/ format like in example
        if not remote_path.startswith("disk:/"):
            remote_path = "disk:/" + remote_path.lstrip("/")

        # Create parent directory
        remote_dir = "/".join(remote_path.split("/")[:-1])
        if remote_dir and remote_dir != "disk:":
            try:
                await self.create_directory(remote_dir)
            except Exception as exc:
                logger.warning("create_directory failed: %s", exc)

        try:
            # Step 1: Get upload URL
            upload_url = await self._get_upload_url(remote_path, overwrite=True)
            logger.info("Got upload URL, uploading file...")
            
            # Step 2: Upload file to the URL - exactly like in example with files parameter
            async with aiofiles.open(local_path, "rb") as f:
                file_content = await f.read()
            
            # Use files parameter exactly like in the example: files={"file": f}
            response = await self._client.put(upload_url, files={"file": file_content})
            
            logger.info("Upload response: %d", response.status_code)
            
            if response.status_code not in (200, 201, 202):
                raise IOError(f"Upload failed: {response.status_code} {response.text}")
            
            if progress_callback:
                progress_callback(file_size, file_size)
            
            logger.info("Upload completed successfully")
            return True

        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise IOError(f"Failed to upload file: {str(e)}")

    async def create_directory(self, disk_path: str) -> bool:
        """Create directory on Yandex.Disk - exactly like in example"""
        if self._client is None:
            raise ConnectionError("Not connected to Yandex.Disk")

        # Ensure path starts with disk:/
        if not disk_path.startswith("disk:/"):
            disk_path = "disk:/" + disk_path.lstrip("/")

        try:
            url = f"{YANDEX_DISK_API_BASE}/resources"
            params = {"path": disk_path}
            
            response = await self._client.put(url, headers=self._headers, params=params)
            
            if response.status_code == 409:
                # Directory already exists - this is ok
                logger.info(f"Directory already exists: {disk_path}")
                return True
            
            if response.status_code not in (200, 201):
                logger.warning(f"Failed to create directory {disk_path}: {response.status_code}")
                return False
            
            logger.info(f"Directory created: {disk_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to create directory {disk_path}: {e}")
            return False

    async def file_exists(self, path: str) -> bool:
        """Check if file or directory exists"""
        if self._client is None:
            raise ConnectionError("Not connected to Yandex.Disk")

        # Ensure path starts with disk:/
        if not path.startswith("disk:/"):
            path = "disk:/" + path.lstrip("/")

        try:
            response = await self._client.get(
                f"{YANDEX_DISK_API_BASE}/resources",
                headers=self._headers,
                params={"path": path}
            )
            return response.status_code == 200
        except Exception:
            return False

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename by replacing invalid characters"""
        invalid_chars = r'[/\\:*?"<>|]'
        sanitized = re.sub(invalid_chars, "_", filename)
        sanitized = sanitized.strip(". ")
        return sanitized or "unnamed"
