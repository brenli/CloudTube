"""
WebDAV Service for Yandex.Disk file storage operations

Uses yadisk library for OAuth token authentication only.

Requirements: 2.1, 2.2, 2.3, 2.5, 2.6, 9.2, 11.3, 11.4
"""

import re
import os
import logging
from dataclasses import dataclass
from typing import Optional, Callable
import yadisk

logger = logging.getLogger(__name__)


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
        self._client: Optional[yadisk.AsyncClient] = None
        self._config: Optional["WebDAVConfig"] = None

    async def connect(self, config: "WebDAVConfig") -> bool:
        """Connect to Yandex.Disk using OAuth token"""
        from bot.database import WebDAVConfig

        if self._client is not None:
            await self.disconnect()

        try:
            # Create yadisk client with OAuth token
            self._client = yadisk.AsyncClient(token=config.password)
            self._config = config
            
            # Test connection
            is_valid = await self._client.check_token()
            
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
            await self._client.close()
            self._client = None
        self._config = None

    async def test_connection(self) -> bool:
        """Test Yandex.Disk connection"""
        if self._client is None:
            return False

        try:
            return await self._client.check_token()
        except Exception:
            return False

    async def get_storage_info(self) -> StorageInfo:
        """Get storage information from Yandex.Disk"""
        if self._client is None:
            return StorageInfo(0, 0, 0, is_connected=False)

        try:
            disk_info = await self._client.get_disk_info()
            total = disk_info.total_space or 0
            used = disk_info.used_space or 0
            return StorageInfo(total, used, total - used, is_connected=True)
        except Exception as e:
            logger.error(f"Failed to get storage info: {e}")
            return StorageInfo(0, 0, 0, is_connected=False)

    async def upload_file(self, local_path: str, remote_path: str,
                         progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        """Upload file to Yandex.Disk"""
        if self._client is None:
            raise ConnectionError("Not connected to Yandex.Disk")

        file_size = os.path.getsize(local_path)
        logger.info("Uploading %s (%.1f MB) → %s", local_path, file_size / 1024 / 1024, remote_path)

        # Ensure remote path starts with /
        if not remote_path.startswith("/"):
            remote_path = "/" + remote_path

        # Create parent directories
        remote_dir = "/".join(remote_path.split("/")[:-1])
        if remote_dir and remote_dir != "/":
            try:
                await self.create_directory(remote_dir)
            except Exception as exc:
                logger.warning("create_directory failed: %s", exc)

        try:
            # Upload file using yadisk library
            await self._client.upload(local_path, remote_path, overwrite=True)
            
            if progress_callback:
                progress_callback(file_size, file_size)
            
            logger.info("Upload completed successfully")
            return True

        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise IOError(f"Failed to upload file: {str(e)}")

    async def create_directory(self, path: str) -> bool:
        """Create directory on Yandex.Disk"""
        if self._client is None:
            raise ConnectionError("Not connected to Yandex.Disk")

        # Ensure path starts with /
        if not path.startswith("/"):
            path = "/" + path

        try:
            # Check if directory already exists
            if await self._client.exists(path):
                return True

            # Create directory recursively
            parts = [p for p in path.split("/") if p]
            current_path = ""
            
            for part in parts:
                current_path += "/" + part
                try:
                    if not await self._client.exists(current_path):
                        await self._client.mkdir(current_path)
                        logger.info(f"Created directory: {current_path}")
                except yadisk.exceptions.PathExistsError:
                    pass
                except Exception as e:
                    logger.warning(f"Failed to create directory {current_path}: {e}")

            return True

        except Exception as e:
            logger.error(f"Failed to create directory {path}: {e}")
            return False

    async def file_exists(self, path: str) -> bool:
        """Check if file or directory exists"""
        if self._client is None:
            raise ConnectionError("Not connected to Yandex.Disk")

        # Ensure path starts with /
        if not path.startswith("/"):
            path = "/" + path

        try:
            return await self._client.exists(path)
        except Exception:
            return False

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename by replacing invalid characters"""
        invalid_chars = r'[/\\:*?"<>|]'
        sanitized = re.sub(invalid_chars, "_", filename)
        sanitized = sanitized.strip(". ")
        return sanitized or "unnamed"
