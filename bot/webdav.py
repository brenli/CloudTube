"""
WebDAV Service for Yandex.Disk file storage operations

Provides WebDAV client functionality for uploading files to Yandex.Disk.
Supports both Basic Auth (username:password) and OAuth token authentication.

Requirements: 2.1, 2.2, 2.3, 2.5, 2.6, 9.2, 11.3, 11.4
"""

import re
from dataclasses import dataclass
from typing import Optional, Callable
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
    """WebDAV service for Yandex.Disk file storage operations"""
    
    def __init__(self):
        """Initialize WebDAV service"""
        self._client: Optional[httpx.AsyncClient] = None
        self._config: Optional['WebDAVConfig'] = None
        self._auth_header: Optional[dict] = None
    
    async def connect(self, config: 'WebDAVConfig') -> bool:
        """
        Connect to Yandex.Disk WebDAV storage
        
        Supports two authentication methods:
        1. Basic Auth: username + password
        2. OAuth Token: username + OAuth token (password field contains token)
        
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
            # Determine authentication method
            # If password starts with "y0_" or "t1.", it's an OAuth token
            is_oauth = config.password.startswith(('y0_', 't1.', 'AQAA'))
            
            if is_oauth:
                # OAuth token authentication
                self._auth_header = {
                    'Authorization': f'OAuth {config.password}'
                }
                auth = None  # Don't use Basic Auth
            else:
                # Basic authentication
                self._auth_header = {}
                auth = (config.username, config.password)
            
            # Create HTTP client
            self._client = httpx.AsyncClient(
                auth=auth,
                timeout=httpx.Timeout(
                    connect=30.0,
                    read=300.0,
                    write=300.0,
                    pool=30.0
                ),
                follow_redirects=True
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
            self._auth_header = None
            raise ConnectionError(f"Failed to connect to Yandex.Disk WebDAV: {str(e)}")
    
    async def disconnect(self) -> None:
        """Disconnect from Yandex.Disk WebDAV storage"""
        if self._client:
            await self._client.aclose()
            self._client = None
        
        self._config = None
        self._auth_header = None
    
    async def test_connection(self) -> bool:
        """
        Test Yandex.Disk WebDAV connection
        
        Returns:
            True if connection is working, False otherwise
        """
        if self._client is None:
            return False
        
        try:
            # Try to list root directory using PROPFIND
            response = await self._client.request(
                "PROPFIND",
                self._config.url,
                headers={**self._auth_header, "Depth": "0"}
            )
            return response.status_code in (200, 207)  # 207 Multi-Status is valid for WebDAV
        except Exception:
            return False

    async def get_storage_info(self) -> StorageInfo:
        """
        Get storage information from Yandex.Disk WebDAV
        
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
            # Send PROPFIND request to get quota information
            response = await self._client.request(
                "PROPFIND",
                self._config.url,
                headers={**self._auth_header, "Depth": "0"},
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
            
            # Parse XML response
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
    async def upload_file(
        self,
        local_path: str,
        remote_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Upload file to Yandex.Disk WebDAV storage using curl
        
        Uses curl in subprocess to avoid Python socket timeout issues
        and WebDAV throttling problems.
        
        Args:
            local_path: Path to local file
            remote_path: Remote path on Yandex.Disk
            progress_callback: Optional callback for progress updates
            
        Returns:
            True if upload successful, False otherwise
        """
        if self._client is None:
            raise ConnectionError("Not connected to Yandex.Disk WebDAV")
        
        try:
            import os
            import logging
            import subprocess
            import urllib.parse
            
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
            
            # Build full URL with proper encoding
            encoded_path = urllib.parse.quote(remote_path)
            full_url = f"{self._config.url.rstrip('/')}/{encoded_path.lstrip('/')}"
            logger.info(f"Upload URL: {full_url}")
            
            # Upload using curl in subprocess
            logger.info("Starting curl upload...")
            
            def _upload_with_curl():
                """Run curl in synchronous context"""
                # Determine if using OAuth or Basic Auth
                is_oauth = self._config.password.startswith(('y0_', 't1.', 'AQAA'))
                
                if is_oauth:
                    # OAuth authentication
                    curl_command = [
                        'curl',
                        '-X', 'PUT',
                        '-H', f'Authorization: OAuth {self._config.password}',
                        '--data-binary', f'@{local_path}',
                        '--max-time', '7200',  # 2 hours
                        '--connect-timeout', '30',
                        '-w', '%{http_code}',
                        '-o', '/dev/null',
                        '-s',
                        full_url
                    ]
                else:
                    # Basic authentication
                    curl_command = [
                        'curl',
                        '-X', 'PUT',
                        '-u', f'{self._config.username}:{self._config.password}',
                        '--data-binary', f'@{local_path}',
                        '--max-time', '7200',
                        '--connect-timeout', '30',
                        '-w', '%{http_code}',
                        '-o', '/dev/null',
                        '-s',
                        full_url
                    ]
                
                logger.info("Running curl command")
                
                result = subprocess.run(
                    curl_command,
                    capture_output=True,
                    text=True,
                    timeout=7200
                )
                
                return result
            
            # Run curl in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, _upload_with_curl)
            
            status_code = result.stdout.strip()
            logger.info(f"Curl completed with status: {status_code}")
            
            if result.returncode != 0:
                logger.error(f"Curl failed with return code: {result.returncode}")
                logger.error(f"Stderr: {result.stderr}")
                raise Exception(f"Curl upload failed (code {result.returncode}): {result.stderr}")
            
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
            
            # Call progress callback
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
        Create directory on Yandex.Disk WebDAV storage
        
        Args:
            path: Directory path to create
            
        Returns:
            True if directory created or already exists, False otherwise
        """
        if self._client is None:
            raise ConnectionError("Not connected to Yandex.Disk WebDAV")
        
        try:
            # Check if directory already exists
            if await self.file_exists(path):
                return True
            
            # Create directory using MKCOL method
            response = await self._client.request(
                "MKCOL",
                f"{self._config.url.rstrip('/')}/{path.lstrip('/')}",
                headers=self._auth_header
            )
            
            return response.status_code in (200, 201)
            
        except Exception:
            return False
    
    async def file_exists(self, path: str) -> bool:
        """
        Check if file or directory exists on Yandex.Disk WebDAV storage
        
        Args:
            path: Path to check
            
        Returns:
            True if file/directory exists, False otherwise
        """
        if self._client is None:
            raise ConnectionError("Not connected to Yandex.Disk WebDAV")
        
        try:
            # Use HEAD request to check existence
            response = await self._client.head(
                f"{self._config.url.rstrip('/')}/{path.lstrip('/')}",
                headers=self._auth_header
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
