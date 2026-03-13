"""
Database layer for the bot

Provides persistent storage for download tasks and WebDAV configuration.
Uses aiosqlite for async SQLite operations and cryptography.fernet for password encryption.

Requirements: 2.4, 3.6, 6.7, 8.4
"""

import aiosqlite
import os
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from cryptography.fernet import Fernet


class TaskStatus(str, Enum):
    """Status of a download task"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"


@dataclass
class NotificationSettings:
    """Notification settings for a download task"""
    notify_start: bool
    notify_progress: bool
    notify_completion: bool
    notify_errors: bool
    
    @classmethod
    def all_notifications(cls) -> 'NotificationSettings':
        """Preset: all notifications"""
        return cls(True, True, True, True)
    
    @classmethod
    def important_only(cls) -> 'NotificationSettings':
        """Preset: only important (start and completion)"""
        return cls(True, False, True, True)
    
    @classmethod
    def errors_only(cls) -> 'NotificationSettings':
        """Preset: only errors"""
        return cls(False, False, False, True)
    
    @classmethod
    def no_notifications(cls) -> 'NotificationSettings':
        """Preset: no notifications"""
        return cls(False, False, False, False)


@dataclass
class DownloadTask:
    """Download task model"""
    task_id: str
    url: str
    video_id: str
    title: str
    quality: str
    status: TaskStatus
    progress: float = 0.0
    file_size: Optional[int] = None
    remote_path: Optional[str] = None
    error_message: Optional[str] = None
    notification_settings: NotificationSettings = None
    playlist_id: Optional[str] = None
    playlist_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize default values"""
        if self.notification_settings is None:
            self.notification_settings = NotificationSettings.important_only()
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = datetime.now(timezone.utc)


@dataclass
class WebDAVConfig:
    """WebDAV configuration model"""
    url: str
    username: str
    password: str


class Database:
    """Database manager for persistent storage"""
    
    def __init__(self, db_path: str, encryption_key: Optional[bytes] = None):
        """
        Initialize database
        
        Args:
            db_path: Path to SQLite database file
            encryption_key: Fernet encryption key for passwords (generated if None)
        """
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
        
        # Initialize encryption
        if encryption_key is None:
            # Generate or load encryption key
            key_path = f"{db_path}.key"
            if os.path.exists(key_path):
                with open(key_path, 'rb') as f:
                    encryption_key = f.read()
            else:
                encryption_key = Fernet.generate_key()
                # Ensure directory exists
                os.makedirs(os.path.dirname(key_path) if os.path.dirname(key_path) else '.', exist_ok=True)
                with open(key_path, 'wb') as f:
                    f.write(encryption_key)
                # Secure the key file
                os.chmod(key_path, 0o600)
        
        self._cipher = Fernet(encryption_key)
    
    async def initialize(self) -> None:
        """Initialize database schema"""
        # Ensure directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        
        self._connection = await aiosqlite.connect(self.db_path)
        
        # Create download_tasks table
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS download_tasks (
                task_id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                video_id TEXT NOT NULL,
                title TEXT NOT NULL,
                quality TEXT NOT NULL,
                status TEXT NOT NULL,
                progress REAL DEFAULT 0.0,
                file_size INTEGER,
                remote_path TEXT,
                error_message TEXT,
                notify_start INTEGER DEFAULT 1,
                notify_progress INTEGER DEFAULT 1,
                notify_completion INTEGER DEFAULT 1,
                notify_errors INTEGER DEFAULT 1,
                playlist_id TEXT,
                playlist_name TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Create webdav_config table
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS webdav_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                url TEXT NOT NULL,
                username TEXT NOT NULL,
                password_encrypted TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Create indexes
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_status 
            ON download_tasks(status)
        """)
        
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_created_at 
            ON download_tasks(created_at DESC)
        """)
        
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_playlist_id 
            ON download_tasks(playlist_id)
        """)
        
        await self._connection.commit()
        
        # Migrate existing tables if needed
        await self._migrate_schema()
    
    async def close(self) -> None:
        """Close database connection"""
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    async def _migrate_schema(self) -> None:
        """Migrate database schema to add new columns if needed"""
        try:
            # Check if playlist_id column exists
            cursor = await self._connection.execute("PRAGMA table_info(download_tasks)")
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # Add playlist_id if missing
            if 'playlist_id' not in column_names:
                await self._connection.execute("""
                    ALTER TABLE download_tasks ADD COLUMN playlist_id TEXT
                """)
            
            # Add playlist_name if missing
            if 'playlist_name' not in column_names:
                await self._connection.execute("""
                    ALTER TABLE download_tasks ADD COLUMN playlist_name TEXT
                """)
            
            await self._connection.commit()
        except Exception:
            # Ignore migration errors (table might not exist yet)
            pass
    
    def _encrypt_password(self, password: str) -> str:
        """Encrypt password using Fernet"""
        return self._cipher.encrypt(password.encode()).decode()
    
    def _decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt password using Fernet"""
        return self._cipher.decrypt(encrypted_password.encode()).decode()
    
    async def save_task(self, task: DownloadTask) -> None:
        """
        Save a new download task
        
        Args:
            task: Download task to save
        """
        await self._connection.execute("""
            INSERT INTO download_tasks (
                task_id, url, video_id, title, quality, status, progress,
                file_size, remote_path, error_message,
                notify_start, notify_progress, notify_completion, notify_errors,
                playlist_id, playlist_name,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task.task_id,
            task.url,
            task.video_id,
            task.title,
            task.quality,
            task.status.value,
            task.progress,
            task.file_size,
            task.remote_path,
            task.error_message,
            int(task.notification_settings.notify_start),
            int(task.notification_settings.notify_progress),
            int(task.notification_settings.notify_completion),
            int(task.notification_settings.notify_errors),
            task.playlist_id,
            task.playlist_name,
            task.created_at.isoformat(),
            task.updated_at.isoformat()
        ))
        await self._connection.commit()
    
    async def update_task(self, task: DownloadTask) -> None:
        """
        Update an existing download task
        
        Args:
            task: Download task to update
        """
        task.updated_at = datetime.now(timezone.utc)
        
        await self._connection.execute("""
            UPDATE download_tasks SET
                url = ?, video_id = ?, title = ?, quality = ?, status = ?,
                progress = ?, file_size = ?, remote_path = ?, error_message = ?,
                notify_start = ?, notify_progress = ?, notify_completion = ?, notify_errors = ?,
                playlist_id = ?, playlist_name = ?,
                updated_at = ?
            WHERE task_id = ?
        """, (
            task.url,
            task.video_id,
            task.title,
            task.quality,
            task.status.value,
            task.progress,
            task.file_size,
            task.remote_path,
            task.error_message,
            int(task.notification_settings.notify_start),
            int(task.notification_settings.notify_progress),
            int(task.notification_settings.notify_completion),
            int(task.notification_settings.notify_errors),
            task.playlist_id,
            task.playlist_name,
            task.updated_at.isoformat(),
            task.task_id
        ))
        await self._connection.commit()
    
    async def get_task(self, task_id: str) -> Optional[DownloadTask]:
        """
        Get a download task by ID
        
        Args:
            task_id: Task ID
            
        Returns:
            Download task or None if not found
        """
        cursor = await self._connection.execute("""
            SELECT task_id, url, video_id, title, quality, status, progress,
                   file_size, remote_path, error_message,
                   notify_start, notify_progress, notify_completion, notify_errors,
                   playlist_id, playlist_name,
                   created_at, updated_at
            FROM download_tasks
            WHERE task_id = ?
        """, (task_id,))
        
        row = await cursor.fetchone()
        if row is None:
            return None
        
        return self._row_to_task(row)
    
    async def get_tasks_by_status(self, status: TaskStatus) -> list[DownloadTask]:
        """
        Get all tasks with a specific status
        
        Args:
            status: Task status to filter by
            
        Returns:
            List of download tasks
        """
        cursor = await self._connection.execute("""
            SELECT task_id, url, video_id, title, quality, status, progress,
                   file_size, remote_path, error_message,
                   notify_start, notify_progress, notify_completion, notify_errors,
                   playlist_id, playlist_name,
                   created_at, updated_at
            FROM download_tasks
            WHERE status = ?
            ORDER BY created_at DESC
        """, (status.value,))
        
        rows = await cursor.fetchall()
        return [self._row_to_task(row) for row in rows]
    
    async def get_all_tasks(self) -> list[DownloadTask]:
        """
        Get all download tasks
        
        Returns:
            List of all download tasks
        """
        cursor = await self._connection.execute("""
            SELECT task_id, url, video_id, title, quality, status, progress,
                   file_size, remote_path, error_message,
                   notify_start, notify_progress, notify_completion, notify_errors,
                   playlist_id, playlist_name,
                   created_at, updated_at
            FROM download_tasks
            ORDER BY created_at DESC
        """)
        
        rows = await cursor.fetchall()
        return [self._row_to_task(row) for row in rows]
    
    def _row_to_task(self, row: tuple) -> DownloadTask:
        """Convert database row to DownloadTask"""
        return DownloadTask(
            task_id=row[0],
            url=row[1],
            video_id=row[2],
            title=row[3],
            quality=row[4],
            status=TaskStatus(row[5]),
            progress=row[6],
            file_size=row[7],
            remote_path=row[8],
            error_message=row[9],
            notification_settings=NotificationSettings(
                notify_start=bool(row[10]),
                notify_progress=bool(row[11]),
                notify_completion=bool(row[12]),
                notify_errors=bool(row[13])
            ),
            playlist_id=row[14],
            playlist_name=row[15],
            created_at=datetime.fromisoformat(row[16]),
            updated_at=datetime.fromisoformat(row[17])
        )
    
    async def save_webdav_config(self, config: WebDAVConfig) -> None:
        """
        Save WebDAV configuration (replaces existing)
        
        Args:
            config: WebDAV configuration to save
        """
        encrypted_password = self._encrypt_password(config.password)
        now = datetime.now(timezone.utc).isoformat()
        
        # Delete existing config
        await self._connection.execute("DELETE FROM webdav_config WHERE id = 1")
        
        # Insert new config
        await self._connection.execute("""
            INSERT INTO webdav_config (id, url, username, password_encrypted, created_at, updated_at)
            VALUES (1, ?, ?, ?, ?, ?)
        """, (config.url, config.username, encrypted_password, now, now))
        
        await self._connection.commit()
    
    async def get_webdav_config(self) -> Optional[WebDAVConfig]:
        """
        Get WebDAV configuration
        
        Returns:
            WebDAV configuration or None if not configured
        """
        cursor = await self._connection.execute("""
            SELECT url, username, password_encrypted
            FROM webdav_config
            WHERE id = 1
        """)
        
        row = await cursor.fetchone()
        if row is None:
            return None
        
        return WebDAVConfig(
            url=row[0],
            username=row[1],
            password=self._decrypt_password(row[2])
        )
