"""
WebDAV Service for file storage operations

Provides WebDAV client functionality for uploading files, managing directories,
and checking storage information.

Requirements: 2.1, 2.2, 2.3, 2.5, 2.6, 9.2, 11.3, 11.4
"""

import re
import os
import logging
import asyncio
import ssl
from dataclasses import dataclass
from typing import Optional, Callable
from urllib.parse import quote
from webdav4.client import Client
import httpx


logger = logging.getLogger(__name__)


@dataclass
class StorageInfo:
    """Storage information"""
    total_space: int  # bytes
    used_space: int
    free_space: int
    is_connected: bool


def _encode_webdav_path(base_url: str, remote_path: str) -> str:
    """
    Build a properly encoded WebDAV URL.

    Each path segment is percent-encoded individually so that
    spaces and special characters are handled correctly while
    slashes are preserved.
    """
    base = base_url.rstrip('/')
    parts = remote_path.strip('/').split('/')
    encoded_parts = [quote(p, safe='') for p in parts if p]
    return f"{base}/{'/'.join(encoded_parts)}"


class WebDAVService:
    """WebDAV service for file storage operations"""

    # Upload configuration
    UPLOAD_CHUNK_SIZE = 8 * 1024 * 1024       # 8 MB chunks for async streaming
    UPLOAD_MAX_RETRIES = 3                      # Number of retry attempts
    UPLOAD_RETRY_DELAY = 5                      # Seconds between retries
    UPLOAD_CONNECT_TIMEOUT = 30.0               # Seconds
    UPLOAD_READ_TIMEOUT = 1800.0                # 30 minutes
    UPLOAD_WRITE_TIMEOUT = 1800.0               # 30 minutes

    def __init__(self):
        """Initialize WebDAV service"""
        self._client: Optional[Client] = None
        self._config: Optional['WebDAVConfig'] = None
        self._http_client: Optional[httpx.AsyncClient] = None

    async def connect(self, config: 'WebDAVConfig') -> bool:
        """
        Connect to WebDAV storage

        Args:
            config: WebDAV configuration

        Returns:
            True if connection successful, False otherwise
        """
        from bot.database import WebDAVConfig

        # Disconnect from existing connection if any
        if self._client is not None:
            await self.disconnect()

        try:
            # Create HTTP client with basic auth and long timeout for large files
            self._http_client = httpx.AsyncClient(
                auth=(config.username, config.password),
                timeout=httpx.Timeout(
                    connect=30.0,
                    read=600.0,
                    write=600.0,
                    pool=30.0
                ),
                follow_redirects=True,
                limits=httpx.Limits(
                    max_connections=10,
                    max_keepalive_connections=5
                )
            )

            # Create WebDAV client
            self._client = Client(
                base_url=config.url,
                auth=(config.username, config.password)
            )

            # Store config
            self._config = config

            # Test connection
            connection_ok = await self.test_connection()

            # If test fails, clean up
            if not connection_ok:
                await self.disconnect()

            return connection_ok

        except Exception as e:
            self._client = None
            self._config = None
            if self._http_client:
                await self._http_client.aclose()
                self._http_client = None
            raise ConnectionError(f"Failed to connect to WebDAV storage: {str(e)}")

    async def disconnect(self) -> None:
        """Disconnect from WebDAV storage"""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

        self._client = None
        self._config = None

    async def test_connection(self) -> bool:
        """
        Test WebDAV connection

        Returns:
            True if connection is working, False otherwise
        """
        if self._client is None or self._http_client is None:
            return False

        try:
            response = await self._http_client.request(
                "PROPFIND", self._config.url, headers={"Depth": "0"}
            )
            return response.status_code in (200, 207)
        except Exception:
            return False

    async def get_storage_info(self) -> StorageInfo:
        """
        Get storage information

        Returns:
            Storage information including space usage
        """
        if self._client is None or self._http_client is None:
            return StorageInfo(
                total_space=0,
                used_space=0,
                free_space=0,
                is_connected=False
            )

        try:
            response = await self._http_client.request(
                "PROPFIND",
                self._config.url,
                headers={"Depth": "0"},
                content="""<?xml version="1.0" encoding="utf-8" ?>
                <D:propfind xmlns:D="DAV:">
                    <D:prop>
                        <D:quota-available-bytes/>
                        <D:quota-used-bytes/>
                    </D:prop>
                </D:propfind>"""
            )

            if response.status_code not in (200, 207):
                return StorageInfo(
                    total_space=0,
                    used_space=0,
                    free_space=0,
                    is_connected=True
                )

            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.text)
            namespaces = {'D': 'DAV:'}

            quota_available = root.find('.//D:quota-available-bytes', namespaces)
            quota_used = root.find('.//D:quota-used-bytes', namespaces)

            free_space = int(quota_available.text) if quota_available is not None and quota_available.text else 0
            used_space = int(quota_used.text) if quota_used is not None and quota_used.text else 0
            total_space = free_space + used_space

            return StorageInfo(
                total_space=total_space,
                used_space=used_space,
                free_space=free_space,
                is_connected=True
            )

        except Exception:
            return StorageInfo(
                total_space=0,
                used_space=0,
                free_space=0,
                is_connected=await self.test_connection()
            )

    async def _upload_with_httpx(
        self,
        local_path: str,
        full_url: str,
        file_size: int,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> int:
        """
        Upload file using httpx async client with async streaming.

        Returns:
            HTTP status code from the server
        """
        # Create a dedicated httpx client for upload with generous timeouts
        async with httpx.AsyncClient(
            auth=(self._config.username, self._config.password),
            timeout=httpx.Timeout(
                connect=self.UPLOAD_CONNECT_TIMEOUT,
                read=self.UPLOAD_READ_TIMEOUT,
                write=self.UPLOAD_WRITE_TIMEOUT,
                pool=60.0
            ),
            follow_redirects=True,
        ) as upload_client:

            # Create async generator for streaming upload
            async def async_file_stream():
                bytes_sent = 0
                # Read file in thread pool to avoid blocking event loop
                loop = asyncio.get_event_loop()

                with open(local_path, 'rb') as f:
                    while True:
                        chunk = await loop.run_in_executor(
                            None, f.read, self.UPLOAD_CHUNK_SIZE
                        )
                        if not chunk:
                            break
                        bytes_sent += len(chunk)
                        if progress_callback:
                            try:
                                progress_callback(bytes_sent, file_size)
                            except Exception:
                                pass
                        yield chunk

            response = await upload_client.put(
                full_url,
                content=async_file_stream(),
                headers={
                    'Content-Type': 'application/octet-stream',
                    'Content-Length': str(file_size),
                },
            )

            logger.info(f"httpx upload response status: {response.status_code}")
            if response.status_code not in (200, 201, 204):
                logger.error(f"Upload failed with status {response.status_code}")
                if response.text:
                    logger.error(f"Response body: {response.text[:500]}")

            return response.status_code

    async def _upload_with_requests(
        self,
        local_path: str,
        full_url: str,
        file_size: int,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> int:
        """
        Upload file using requests library in a thread pool (fallback).

        Uses a plain file object so requests sends Content-Length header
        instead of chunked transfer encoding (which Yandex.Disk rejects).

        Returns:
            HTTP status code from the server
        """
        import requests as req_lib

        def _sync_upload() -> int:
            session = req_lib.Session()
            try:
                # Open file as a plain binary file object
                # requests will use Content-Length (not chunked) when given a file object
                with open(local_path, 'rb') as f:
                    response = session.put(
                        full_url,
                        data=f,
                        auth=(self._config.username, self._config.password),
                        timeout=(self.UPLOAD_CONNECT_TIMEOUT, self.UPLOAD_WRITE_TIMEOUT),
                        headers={
                            'Content-Type': 'application/octet-stream',
                            'Content-Length': str(file_size),
                        },
                    )

                logger.info(f"requests upload response status: {response.status_code}")
                if response.status_code not in (200, 201, 204):
                    logger.error(f"Upload failed with status {response.status_code}")
                    if response.text:
                        logger.error(f"Response body: {response.text[:500]}")

                # Report final progress
                if progress_callback:
                    try:
                        progress_callback(file_size, file_size)
                    except Exception:
                        pass

                return response.status_code

            finally:
                session.close()

        # Run synchronous upload in thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_upload)

    async def _upload_with_curl(
        self,
        local_path: str,
        full_url: str,
        file_size: int,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> int:
        """
        Upload file using curl subprocess as last-resort fallback.

        curl handles SSL and large file uploads very reliably.

        Returns:
            HTTP status code (0 if curl failed to execute)
        """
        try:
            cmd = [
                'curl', '-s', '-o', '/dev/null',
                '-w', '%{http_code}',
                '-T', local_path,
                '-u', f'{self._config.username}:{self._config.password}',
                '--connect-timeout', str(int(self.UPLOAD_CONNECT_TIMEOUT)),
                '--max-time', str(int(self.UPLOAD_WRITE_TIMEOUT)),
                full_url
            ]

            logger.info("Starting curl upload...")
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"curl failed with return code {process.returncode}")
                if stderr:
                    logger.error(f"curl stderr: {stderr.decode(errors='replace')[:500]}")
                return 0

            status_code = int(stdout.decode().strip())
            logger.info(f"curl upload response status: {status_code}")

            if status_code in (200, 201, 204) and progress_callback:
                try:
                    progress_callback(file_size, file_size)
                except Exception:
                    pass

            return status_code

        except FileNotFoundError:
            logger.warning("curl not found on system, skipping curl fallback")
            return 0
        except Exception as e:
            logger.error(f"curl upload failed: {e}")
            return 0

    async def upload_file(
        self,
        local_path: str,
        remote_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Upload file to WebDAV storage with retry logic.

        Tries multiple upload methods in order:
        1. httpx async streaming
        2. requests with file object (in thread pool)
        3. curl subprocess

        Retries up to UPLOAD_MAX_RETRIES times.

        Args:
            local_path: Path to local file
            remote_path: Remote path on WebDAV storage
            progress_callback: Optional callback for progress updates (bytes_uploaded, total_bytes)

        Returns:
            True if upload successful, False otherwise

        Raises:
            ConnectionError: If not connected to WebDAV storage
            IOError: If upload fails after all retries
        """
        if self._client is None or self._http_client is None:
            raise ConnectionError("Not connected to WebDAV storage")

        file_size = os.path.getsize(local_path)
        logger.info(
            f"Uploading file: {local_path} "
            f"({file_size} bytes / {file_size / 1024 / 1024:.1f} MB) "
            f"to {remote_path}"
        )

        # Create directory if needed
        remote_dir = '/'.join(remote_path.split('/')[:-1])
        if remote_dir:
            logger.info(f"Creating directory: {remote_dir}")
            try:
                await self.create_directory(remote_dir)
            except Exception as e:
                logger.warning(f"Failed to create directory (may already exist): {e}")

        # Build properly encoded URL
        full_url = _encode_webdav_path(self._config.url, remote_path)
        logger.info(f"Upload URL: {full_url}")

        last_error: Optional[Exception] = None

        # Define upload methods to try in order
        upload_methods = [
            ("httpx", self._upload_with_httpx),
            ("requests", self._upload_with_requests),
            ("curl", self._upload_with_curl),
        ]

        for attempt in range(1, self.UPLOAD_MAX_RETRIES + 1):
            logger.info(f"Upload attempt {attempt}/{self.UPLOAD_MAX_RETRIES}")

            for method_name, method_func in upload_methods:
                try:
                    logger.info(f"Trying upload with {method_name}...")
                    status = await method_func(
                        local_path, full_url, file_size, progress_callback
                    )
                    if status in (200, 201, 204):
                        if progress_callback:
                            try:
                                progress_callback(file_size, file_size)
                            except Exception:
                                pass
                        logger.info(f"Upload completed successfully via {method_name}")
                        return True
                    else:
                        msg = f"{method_name} upload returned status {status}"
                        last_error = IOError(msg)
                        logger.warning(msg)

                except Exception as e:
                    last_error = e
                    logger.warning(f"{method_name} upload failed: {e}")

            # Wait before retrying (except on last attempt)
            if attempt < self.UPLOAD_MAX_RETRIES:
                delay = self.UPLOAD_RETRY_DELAY * attempt
                logger.info(f"Waiting {delay}s before retry...")
                await asyncio.sleep(delay)

        # All retries exhausted
        error_msg = f"Failed to upload file after {self.UPLOAD_MAX_RETRIES} attempts: {last_error}"
        logger.error(error_msg)
        raise IOError(error_msg)

    async def create_directory(self, path: str) -> bool:
        """
        Create directory on WebDAV storage (recursive).

        Creates all parent directories as needed.

        Args:
            path: Directory path to create

        Returns:
            True if directory created or already exists, False otherwise
        """
        if self._client is None or self._http_client is None:
            raise ConnectionError("Not connected to WebDAV storage")

        try:
            # Check if directory already exists
            if await self.file_exists(path):
                return True

            # Create parent directories recursively
            parts = path.strip('/').split('/')
            current_path = ""
            for part in parts:
                current_path = f"{current_path}/{part}" if current_path else part
                if not await self.file_exists(current_path):
                    encoded_url = _encode_webdav_path(self._config.url, current_path)
                    response = await self._http_client.request("MKCOL", encoded_url)
                    if response.status_code not in (200, 201, 405):
                        logger.warning(
                            f"MKCOL {current_path} returned {response.status_code}"
                        )

            return True

        except Exception as e:
            logger.warning(f"create_directory failed: {e}")
            return False

    async def file_exists(self, path: str) -> bool:
        """
        Check if file or directory exists on WebDAV storage

        Args:
            path: Path to check

        Returns:
            True if file/directory exists, False otherwise
        """
        if self._client is None or self._http_client is None:
            raise ConnectionError("Not connected to WebDAV storage")

        try:
            encoded_url = _encode_webdav_path(self._config.url, path)
            response = await self._http_client.head(encoded_url)
            return response.status_code == 200

        except Exception:
            return False

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename by replacing invalid characters

        Args:
            filename: Original filename

        Returns:
            Sanitized filename with invalid characters replaced by underscores
        """
        invalid_chars = r'[/\\:*?"<>|]'
        sanitized = re.sub(invalid_chars, '_', filename)
        sanitized = sanitized.strip('. ')

        if not sanitized:
            sanitized = "unnamed"

        return sanitized