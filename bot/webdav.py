"""
WebDAV Service for file storage operations

Provides Yandex.Disk REST API client functionality for uploading files, managing directories,
and checking storage information.

Requirements: 2.1, 2.2, 2.3, 2.5, 2.6, 9.2, 11.3, 11.4
"""

import re
from dataclasses import dataclass
from typing import Optional, Callable
import yadisk
import asyncio


@dataclass
class StorageInfo:
    """Storage information"""
    total_space: int  # bytes
    used_space: int
    free_space: int
    is_connected: bool


class WebDAVService:
    """Yandex.Disk service for file storage operations"""
    
    def __init__(self):
        """Initialize Yandex.Disk service"""
        self._client: Optional[yadisk.AsyncClient] = None
        self._config: Optional['WebDAVConfig'] = None
    
    async def connect(self, config: 'WebDAVConfig') -> bool:
        """
        Connect to Yandex.Disk storage
        
        Args:
            config: WebDAV configuration (uses password as OAuth token)
            
        Returns:
            True if connection successful, False otherwise
        """
        from bot.database import WebDAVConfig
        
        # Disconnect from existing connection if any
        if self._client is not None:
            await self.disconnect()
        
        try:
            # Create Yandex.Disk client with OAuth token
            # Note: config.password should contain OAuth token for Yandex.Disk
            self._client = yadisk.AsyncClient(token=config.password)
            
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
            raise ConnectionError(f"Failed to connect to Yandex.Disk: {str(e)}")
    
    async def disconnect(self) -> None:
        """Disconnect from Yandex.Disk storage"""
        if self._client:
            await self._client.close()
            self._client = None
        
        self._config = None
    
    async def test_connection(self) -> bool:
        """
        Test Yandex.Disk connection
        
        Returns:
            True if connection is working, False otherwise
        """
        if self._client is None:
            return False
        
        try:
            # Try to check token
            return await self._client.check_token()
        except Exception:
            return False

    async def get_storage_info(self) -> StorageInfo:
        """
        Get storage information
        
        Returns:
            Storage information including space usage
        """
        if self._client is None:
            return StorageInfo(
                total_space=0,
                used_space=0,
                free_space=0,
                is_connected=False
            )
        
        try:
            # Get disk info from Yandex.Disk API
            disk_info = await self._client.get_disk_info()
            
            total_space = disk_info.total_space or 0
            used_space = disk_info.used_space or 0
            free_space = total_space - used_space
            
            return StorageInfo(
                total_space=total_space,
                used_space=used_space,
                free_space=free_space,
                is_connected=True
            )
            
        except Exception:
            # If we can't get disk info, return connected status with unknown space
            return StorageInfo(
                total_space=0,
                used_space=0,
                free_space=0,
                is_connected=await self.test_connection()
            )
    async def upload_file(
        self,
        local_path: str,
        remote_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Upload file to Yandex.Disk storage using REST API
        
        Args:
            local_path: Path to local file
            remote_path: Remote path on Yandex.Disk (e.g., "Single Videos/video.mp4")
            progress_callback: Optional callback for progress updates (bytes_uploaded, total_bytes)
            
        Returns:
            True if upload successful, False otherwise
        """
        if self._client is None:
            raise ConnectionError("Not connected to Yandex.Disk")
        
        try:
            import os
            import logging
            
            logger = logging.getLogger(__name__)
            
            # Get file size
            file_size = os.path.getsize(local_path)
            logger.info(f"Uploading file: {local_path} ({file_size} bytes / {file_size/1024/1024:.1f} MB) to {remote_path}")
            
            # Ensure remote path starts with /
            if not remote_path.startswith('/'):
                remote_path = '/' + remote_path
            
            # Create directory if needed
            remote_dir = '/'.join(remote_path.split('/')[:-1])
            if remote_dir and remote_dir != '/':
                logger.info(f"Creating directory: {remote_dir}")
                try:
                    await self.create_directory(remote_dir)
                except Exception as e:
                    logger.warning(f"Failed to create directory (may already exist): {e}")
            
            logger.info(f"Starting upload to: {remote_path}")
            
            # Upload file using Yandex.Disk REST API
            # This bypasses WebDAV throttling issues
            await self._client.upload(local_path, remote_path, overwrite=True)
            
            logger.info("Upload completed successfully")
            
            # Call progress callback with final progress
            if progress_callback:
                progress_callback(file_size, file_size)
            
            return True
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to upload file: {str(e)}", exc_info=True)
            raise IOError(f"Failed to upload file: {str(e)}")
    
    async def create_directory(self, path: str) -> bool:
        """
        Create directory on Yandex.Disk storage
        
        Args:
            path: Directory path to create
            
        Returns:
            True if directory created or already exists, False otherwise
        """
        if self._client is None:
            raise ConnectionError("Not connected to Yandex.Disk")
        
        try:
            # Ensure path starts with /
            if not path.startswith('/'):
                path = '/' + path
            
            # Check if directory already exists
            if await self.file_exists(path):
                return True
            
            # Create directory
            await self._client.mkdir(path)
            return True
            
        except yadisk.exceptions.PathExistsError:
            # Directory already exists
            return True
        except Exception:
            return False
    
    async def file_exists(self, path: str) -> bool:
        """
        Check if file or directory exists on Yandex.Disk storage
        
        Args:
            path: Path to check
            
        Returns:
            True if file/directory exists, False otherwise
        """
        if self._client is None:
            raise ConnectionError("Not connected to Yandex.Disk")
        
        try:
            # Ensure path starts with /
            if not path.startswith('/'):
                path = '/' + path
            
            # Check if path exists
            return await self._client.exists(path)
            
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
        # Replace invalid characters with underscores
        # Invalid characters: / \ : * ? " < > |
        invalid_chars = r'[/\\:*?"<>|]'
        sanitized = re.sub(invalid_chars, '_', filename)
        
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip('. ')
        
        # Ensure filename is not empty
        if not sanitized:
            sanitized = "unnamed"
        
        return sanitized
