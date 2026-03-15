"""
WebDAV Service for file storage operations

Provides WebDAV client functionality for uploading files, managing directories,
and checking storage information.

Requirements: 2.1, 2.2, 2.3, 2.5, 2.6, 9.2, 11.3, 11.4
"""

import re
from dataclasses import dataclass
from typing import Optional, Callable
from webdav4.client import Client
import httpx
import asyncio


@dataclass
class StorageInfo:
    """Storage information"""
    total_space: int  # bytes
    used_space: int
    free_space: int
    is_connected: bool


class WebDAVService:
    """WebDAV service for file storage operations"""
    
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
            # Create HTTP client with basic auth
            self._http_client = httpx.AsyncClient(
                auth=(config.username, config.password),
                timeout=httpx.Timeout(
                    connect=30.0,
                    read=30.0,
                    write=30.0,
                    pool=30.0
                ),
                follow_redirects=True
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
            # Try to list root directory
            response = await self._http_client.request("PROPFIND", self._config.url, headers={"Depth": "0"})
            return response.status_code in (200, 207)  # 207 Multi-Status is also valid
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
            # Send PROPFIND request to get quota information
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
                # If quota info not available, return connected status with unknown space
                return StorageInfo(
                    total_space=0,
                    used_space=0,
                    free_space=0,
                    is_connected=True
                )
            
            # Parse XML response to extract quota information
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.text)
            
            # Define namespaces
            namespaces = {'D': 'DAV:'}
            
            # Extract quota information
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
            # If we can't get quota info, return connected status with unknown space
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
        Upload file to WebDAV storage using curl in subprocess
        
        Args:
            local_path: Path to local file
            remote_path: Remote path on WebDAV storage
            progress_callback: Optional callback for progress updates (bytes_uploaded, total_bytes)
            
        Returns:
            True if upload successful, False otherwise
        """
        if self._client is None or self._http_client is None:
            raise ConnectionError("Not connected to WebDAV storage")
        
        try:
            import os
            import logging
            import subprocess
            
            logger = logging.getLogger(__name__)
            
            # Get file size
            file_size = os.path.getsize(local_path)
            logger.info(f"Uploading file: {local_path} ({file_size} bytes / {file_size/1024/1024:.1f} MB) to {remote_path}")
            
            # Create directory if needed
            remote_dir = '/'.join(remote_path.split('/')[:-1])
            if remote_dir:
                logger.info(f"Creating directory: {remote_dir}")
                try:
                    await self.create_directory(remote_dir)
                except Exception as e:
                    logger.warning(f"Failed to create directory (may already exist): {e}")
            
            # Build full URL
            full_url = f"{self._config.url.rstrip('/')}/{remote_path.lstrip('/')}"
            logger.info(f"Upload URL: {full_url}")
            
            # Upload file using curl in subprocess
            # Curl doesn't have Python's socket timeout issues
            logger.info("Starting curl upload in subprocess...")
            
            def _upload_with_curl():
                """Run curl in synchronous context"""
                curl_command = [
                    'curl',
                    '-X', 'PUT',
                    '-u', f'{self._config.username}:{self._config.password}',
                    '--data-binary', f'@{local_path}',
                    '--max-time', '7200',  # 2 hours timeout
                    '--connect-timeout', '30',
                    '-w', '%{http_code}',  # Output HTTP status code
                    '-o', '/dev/null',  # Discard response body
                    '-s',  # Silent mode
                    full_url
                ]
                
                logger.info("Running curl command")
                
                result = subprocess.run(
                    curl_command,
                    capture_output=True,
                    text=True,
                    timeout=7200  # 2 hours
                )
                
                return result
            
            # Run curl in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, _upload_with_curl)
            
            status_code = result.stdout.strip()
            logger.info(f"Curl completed with status: {status_code}")
            
            if result.returncode != 0:
                logger.error(f"Curl failed with return code: {result.returncode}")
                logger.error(f"Stderr: {result.stderr}")
                raise Exception(f"Curl upload failed: {result.stderr}")
            
            # Parse status code
            try:
                http_status = int(status_code)
            except ValueError:
                logger.error(f"Invalid HTTP status code: {status_code}")
                raise Exception(f"Invalid HTTP status code: {status_code}")
            
            logger.info(f"Upload response status: {http_status}")
            
            if http_status not in (200, 201, 204):
                logger.error(f"Upload failed with status {http_status}")
                return False
            
            # Call progress callback with final progress
            if progress_callback:
                progress_callback(file_size, file_size)
            
            logger.info("Upload completed successfully")
            return True
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to upload file: {str(e)}", exc_info=True)
            raise IOError(f"Failed to upload file: {str(e)}")
    
    async def create_directory(self, path: str) -> bool:
        """
        Create directory on WebDAV storage
        
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
            
            # Create directory using MKCOL method
            response = await self._http_client.request(
                "MKCOL",
                f"{self._config.url.rstrip('/')}/{path.lstrip('/')}"
            )
            
            return response.status_code in (200, 201)
            
        except Exception:
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
            # Use HEAD request to check existence
            response = await self._http_client.head(
                f"{self._config.url.rstrip('/')}/{path.lstrip('/')}"
            )
            
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
