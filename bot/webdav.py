"""
WebDAV Service for file storage operations

Mounts Yandex.Disk via davfs2 and uses simple file operations.

Requirements: 2.1, 2.2, 2.3, 2.5, 2.6, 9.2, 11.3, 11.4
"""

import re
import os
import pwd
import shutil
import asyncio
import logging
from dataclasses import dataclass
from typing import Optional, Callable
from pathlib import Path

logger = logging.getLogger(__name__)

MOUNT_POINT = "/mnt/yandex-disk"
# DAVFS2 paths will be set dynamically in _setup_davfs2()
DAVFS2_SECRETS = None
DAVFS2_CONFIG = None


@dataclass
class StorageInfo:
    """Storage information"""
    total_space: int  # bytes
    used_space: int
    free_space: int
    is_connected: bool


class WebDAVService:
    """WebDAV service using davfs2 mount"""

    def __init__(self):
        """Initialize WebDAV service"""
        self._config: Optional['WebDAVConfig'] = None
        self._is_mounted: bool = False

    async def connect(self, config: 'WebDAVConfig') -> bool:
        """
        Connect to WebDAV storage by mounting it

        Args:
            config: WebDAV configuration

        Returns:
            True if connection successful, False otherwise
        """
        from bot.database import WebDAVConfig

        # Disconnect from existing connection if any
        if self._is_mounted:
            await self.disconnect()

        try:
            self._config = config

            # Create mount point with sudo if doesn't exist
            if not os.path.exists(MOUNT_POINT):
                logger.info(f"Creating mount point {MOUNT_POINT}")
                process = await asyncio.create_subprocess_shell(
                    f"sudo mkdir -p {MOUNT_POINT}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
                
                # Set owner to current user
                uid = os.getuid()
                user_info = pwd.getpwuid(uid)
                username = user_info.pw_name
                
                logger.info(f"Setting owner of {MOUNT_POINT} to {username}")
                process = await asyncio.create_subprocess_shell(
                    f"sudo chown {username}:{username} {MOUNT_POINT}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
                logger.info(f"Mount point owner set successfully")

            # Setup davfs2 configuration
            await self._setup_davfs2()

            # Save credentials
            await self._save_credentials()

            # Mount WebDAV
            success = await self._mount_webdav()

            if not success:
                logger.error("Failed to mount WebDAV")
                return False

            self._is_mounted = True
            logger.info(f"WebDAV mounted successfully at {MOUNT_POINT}")

            # Test connection
            connection_ok = await self.test_connection()

            if not connection_ok:
                await self.disconnect()
                return False

            return True

        except Exception as e:
            logger.error(f"Failed to connect to WebDAV storage: {str(e)}")
            await self.disconnect()
            raise ConnectionError(f"Failed to connect to WebDAV storage: {str(e)}")

    async def _setup_davfs2(self) -> None:
        """Setup davfs2 configuration"""
        try:
            # Get home directory of the user running the process
            # Get current process user ID
            uid = os.getuid()
            user_info = pwd.getpwuid(uid)
            home_dir = user_info.pw_dir
            
            logger.info(f"Running as user: {user_info.pw_name} (uid={uid})")
            logger.info(f"User home directory: {home_dir}")
            
            davfs2_dir = os.path.join(home_dir, '.davfs2')
            logger.info(f"Using davfs2 directory: {davfs2_dir}")
            
            # Create .davfs2 directory
            os.makedirs(davfs2_dir, exist_ok=True)

            # Update paths to use correct home directory
            global DAVFS2_SECRETS, DAVFS2_CONFIG
            DAVFS2_SECRETS = os.path.join(davfs2_dir, 'secrets')
            DAVFS2_CONFIG = os.path.join(davfs2_dir, 'davfs2.conf')

            # Create config file if doesn't exist
            if not os.path.exists(DAVFS2_CONFIG):
                config_content = """# davfs2 configuration
use_locks 0
cache_size 50
delay_upload 0
"""
                with open(DAVFS2_CONFIG, 'w') as f:
                    f.write(config_content)
                logger.info(f"Created davfs2 config: {DAVFS2_CONFIG}")

        except Exception as e:
            logger.error(f"Failed to setup davfs2: {e}", exc_info=True)
            raise

    async def _save_credentials(self) -> None:
        """Save WebDAV credentials to davfs2 secrets file"""
        try:
            # DAVFS2_SECRETS should be already set by _setup_davfs2
            secrets_content = f"{self._config.url} {self._config.username} {self._config.password}\n"

            logger.info(f"Saving credentials to {DAVFS2_SECRETS}")
            
            with open(DAVFS2_SECRETS, 'w') as f:
                f.write(secrets_content)

            # Set proper permissions (600)
            os.chmod(DAVFS2_SECRETS, 0o600)

            logger.info(f"Credentials saved successfully")

        except Exception as e:
            logger.error(f"Failed to save credentials: {e}", exc_info=True)
            raise

    async def _mount_webdav(self) -> bool:
        """Mount WebDAV using davfs2"""
        try:
            # Check if already mounted
            if await self._is_mounted_check():
                logger.info("WebDAV already mounted")
                return True

            # Get current user and group from process UID
            uid = os.getuid()
            user_info = pwd.getpwuid(uid)
            gid = user_info.pw_gid
            username = user_info.pw_name
            
            logger.info(f"Mounting as user: {username} (uid={uid}, gid={gid})")

            # Mount command with sudo and uid/gid options
            cmd = f"sudo mount -t davfs {self._config.url} {MOUNT_POINT} -o uid={uid},gid={gid}"

            logger.info(f"Mounting WebDAV: {cmd}")

            # Execute mount command
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE
            )

            # Send empty line for any prompts (credentials should be in secrets file)
            stdout, stderr = await process.communicate(input=b'\n\n')

            logger.info(f"Mount stdout: {stdout.decode()}")
            logger.info(f"Mount stderr: {stderr.decode()}")
            logger.info(f"Mount return code: {process.returncode}")

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"Mount failed: {error_msg}")
                return False

            logger.info("Mount command completed successfully")

            # Wait a bit for mount to complete
            await asyncio.sleep(2)

            # Verify mount
            is_mounted = await self._is_mounted_check()
            logger.info(f"Mount verification: {is_mounted}")
            
            return is_mounted

        except Exception as e:
            logger.error(f"Failed to mount WebDAV: {e}", exc_info=True)
            return False

    async def _is_mounted_check(self) -> bool:
        """Check if WebDAV is currently mounted"""
        try:
            # Check if mount point exists and is accessible
            if not os.path.exists(MOUNT_POINT):
                return False

            # Try to list directory
            try:
                os.listdir(MOUNT_POINT)
                return True
            except OSError:
                return False

        except Exception:
            return False

    async def disconnect(self) -> None:
        """Disconnect from WebDAV storage by unmounting"""
        if not self._is_mounted:
            return

        try:
            logger.info(f"Unmounting WebDAV from {MOUNT_POINT}")

            # Unmount command with sudo
            cmd = f"sudo umount {MOUNT_POINT}"

            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                # Try force unmount
                logger.warning("Normal unmount failed, trying force unmount")
                cmd = f"sudo umount -l {MOUNT_POINT}"
                process = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()

            self._is_mounted = False
            logger.info("WebDAV unmounted successfully")

        except Exception as e:
            logger.error(f"Failed to unmount WebDAV: {e}")

        self._config = None

    async def test_connection(self) -> bool:
        """
        Test WebDAV connection

        Returns:
            True if connection is working, False otherwise
        """
        if not self._is_mounted:
            return False

        try:
            # Try to list mount point
            os.listdir(MOUNT_POINT)
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    async def get_storage_info(self) -> StorageInfo:
        """
        Get storage information

        Returns:
            Storage information including space usage
        """
        if not self._is_mounted:
            return StorageInfo(
                total_space=0,
                used_space=0,
                free_space=0,
                is_connected=False
            )

        try:
            # Get disk usage statistics
            stat = os.statvfs(MOUNT_POINT)

            total_space = stat.f_blocks * stat.f_frsize
            free_space = stat.f_bavail * stat.f_frsize
            used_space = total_space - free_space

            return StorageInfo(
                total_space=total_space,
                used_space=used_space,
                free_space=free_space,
                is_connected=True
            )

        except Exception as e:
            logger.error(f"Failed to get storage info: {e}")
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
        Upload file to WebDAV storage by copying to mounted directory

        Args:
            local_path: Path to local file
            remote_path: Remote path on WebDAV storage
            progress_callback: Optional callback for progress updates (bytes_uploaded, total_bytes)

        Returns:
            True if upload successful, False otherwise
        """
        if not self._is_mounted:
            raise ConnectionError("Not connected to WebDAV storage")

        try:
            # Get file size
            file_size = os.path.getsize(local_path)
            logger.info(f"Uploading file: {local_path} ({file_size} bytes / {file_size/1024/1024:.1f} MB) to {remote_path}")

            # Build full destination path
            dest_path = os.path.join(MOUNT_POINT, remote_path.lstrip('/'))

            # Create directory if needed
            dest_dir = os.path.dirname(dest_path)
            if dest_dir:
                logger.info(f"Creating directory: {dest_dir}")
                os.makedirs(dest_dir, exist_ok=True)

            # Copy file with progress tracking for large files
            logger.info(f"Copying file to {dest_path}")
            
            if file_size > 10 * 1024 * 1024 and progress_callback:  # > 10MB
                # Copy in chunks with progress
                chunk_size = 1024 * 1024  # 1MB chunks
                bytes_copied = 0
                
                with open(local_path, 'rb') as src:
                    with open(dest_path, 'wb') as dst:
                        while True:
                            chunk = src.read(chunk_size)
                            if not chunk:
                                break
                            dst.write(chunk)
                            bytes_copied += len(chunk)
                            
                            # Call progress callback
                            if progress_callback:
                                await progress_callback(bytes_copied, file_size)
                            
                            # Small delay to avoid blocking
                            if bytes_copied % (10 * 1024 * 1024) == 0:  # Every 10MB
                                await asyncio.sleep(0.01)
            else:
                # Small file, copy directly
                shutil.copy2(local_path, dest_path)
                
                # Call progress callback with final progress
                if progress_callback:
                    await progress_callback(file_size, file_size)

            logger.info("Upload completed successfully")
            return True

        except Exception as e:
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
        if not self._is_mounted:
            raise ConnectionError("Not connected to WebDAV storage")

        try:
            # Build full path
            full_path = os.path.join(MOUNT_POINT, path.lstrip('/'))

            # Create directory
            os.makedirs(full_path, exist_ok=True)

            return True

        except Exception as e:
            logger.error(f"Failed to create directory: {e}")
            return False

    async def file_exists(self, path: str) -> bool:
        """
        Check if file or directory exists on WebDAV storage

        Args:
            path: Path to check

        Returns:
            True if file/directory exists, False otherwise
        """
        if not self._is_mounted:
            raise ConnectionError("Not connected to WebDAV storage")

        try:
            # Build full path
            full_path = os.path.join(MOUNT_POINT, path.lstrip('/'))

            return os.path.exists(full_path)

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
