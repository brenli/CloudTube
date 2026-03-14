"""
Notification Service for the bot

Handles sending notifications to the owner about download events.
Respects notification settings for each download task.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
"""

from typing import Optional, Callable, Awaitable
from bot.database import DownloadTask, NotificationSettings


class NotificationService:
    """Service for sending notifications to the bot owner"""
    
    def __init__(self):
        """Initialize notification service"""
        self._bot = None
        self._owner_id = None
    
    def set_bot(self, bot):
        """
        Set bot application for sending messages
        
        Args:
            bot: Telegram bot application
        """
        self._bot = bot
    
    def set_owner_id(self, owner_id: int):
        """
        Set owner ID for sending messages
        
        Args:
            owner_id: Telegram user ID of the owner
        """
        self._owner_id = owner_id
    
    async def _send_message(self, message: str) -> None:
        """
        Send message to owner
        
        Args:
            message: Message text to send
        """
        if self._bot and self._owner_id:
            try:
                await self._bot.bot.send_message(
                    chat_id=self._owner_id,
                    text=message
                )
            except Exception as e:
                print(f"Failed to send notification: {e}")
    
    async def notify_download_start(self, task: DownloadTask) -> None:
        """
        Send notification about download start
        
        Args:
            task: Download task that started
        """
        if not task.notification_settings.notify_start:
            return
        
        message = (
            f"🚀 Загрузка начата\n\n"
            f"📹 {task.title}\n"
            f"🎬 Качество: {task.quality}\n"
            f"🆔 ID задачи: {task.task_id}"
        )
        await self._send_message(message)
    
    async def notify_download_progress(self, task: DownloadTask, progress: float) -> None:
        """
        Send notification about download progress
        
        Args:
            task: Download task in progress
            progress: Progress value (0.0 - 1.0)
        """
        if not task.notification_settings.notify_progress:
            return
        
        percent = int(progress * 100)
        message = (
            f"⏳ Прогресс загрузки: {percent}%\n\n"
            f"📹 {task.title}\n"
            f"🆔 ID задачи: {task.task_id}"
        )
        await self._send_message(message)
    
    async def notify_download_complete(self, task: DownloadTask, remote_path: str) -> None:
        """
        Send notification about download completion
        
        Args:
            task: Completed download task
            remote_path: Path where file was saved in storage
        """
        if not task.notification_settings.notify_completion:
            return
        
        file_size_mb = task.file_size / (1024 * 1024) if task.file_size else 0
        message = (
            f"✅ Загрузка завершена\n\n"
            f"📹 {task.title}\n"
            f"📁 Путь: {remote_path}\n"
            f"📦 Размер: {file_size_mb:.2f} MB\n"
            f"🆔 ID задачи: {task.task_id}"
        )
        await self._send_message(message)
    
    async def notify_download_error(self, task: DownloadTask, error: str) -> None:
        """
        Send notification about download error
        
        Args:
            task: Failed download task
            error: Error message
        """
        if not task.notification_settings.notify_errors:
            return
        
        message = (
            f"❌ Ошибка загрузки\n\n"
            f"📹 {task.title}\n"
            f"⚠️ Ошибка: {error}\n"
            f"🆔 ID задачи: {task.task_id}"
        )
        await self._send_message(message)
    
    async def notify_storage_disconnected(self) -> None:
        """Send notification about storage disconnection"""
        message = (
            f"⚠️ Хранилище недоступно\n\n"
            f"Соединение с WebDAV хранилищем потеряно.\n"
            f"Активные загрузки приостановлены."
        )
        await self._send_message(message)
    
    async def notify_storage_full(self, task: DownloadTask) -> None:
        """
        Send notification about storage being full
        
        Args:
            task: Download task that was paused due to full storage
        """
        message = (
            f"💾 Недостаточно места в хранилище\n\n"
            f"📹 {task.title}\n"
            f"Загрузка приостановлена из-за нехватки места.\n"
            f"🆔 ID задачи: {task.task_id}"
        )
        await self._send_message(message)
