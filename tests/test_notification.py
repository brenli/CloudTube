"""
Unit tests for Notification Service

Tests notification presets and message sending based on settings.
Requirements: 6.4, 6.5
"""

import pytest
from bot.notification import NotificationService
from bot.database import DownloadTask, NotificationSettings, TaskStatus


class TestNotificationPresets:
    """Test notification preset configurations"""
    
    def test_all_notifications_preset(self):
        """Test that all_notifications preset enables all notification types"""
        settings = NotificationSettings.all_notifications()
        
        assert settings.notify_start is True
        assert settings.notify_progress is True
        assert settings.notify_completion is True
        assert settings.notify_errors is True
    
    def test_important_only_preset(self):
        """Test that important_only preset enables start, completion, and errors"""
        settings = NotificationSettings.important_only()
        
        assert settings.notify_start is True
        assert settings.notify_progress is False
        assert settings.notify_completion is True
        assert settings.notify_errors is True
    
    def test_errors_only_preset(self):
        """Test that errors_only preset enables only error notifications"""
        settings = NotificationSettings.errors_only()
        
        assert settings.notify_start is False
        assert settings.notify_progress is False
        assert settings.notify_completion is False
        assert settings.notify_errors is True
    
    def test_no_notifications_preset(self):
        """Test that no_notifications preset disables all notifications"""
        settings = NotificationSettings.no_notifications()
        
        assert settings.notify_start is False
        assert settings.notify_progress is False
        assert settings.notify_completion is False
        assert settings.notify_errors is False


class TestNotificationService:
    """Test notification service message sending"""
    
    @pytest.mark.asyncio
    async def test_notify_download_start_when_enabled(self):
        """Test that start notification is sent when enabled"""
        messages = []
        
        async def mock_send(msg: str):
            messages.append(msg)
        
        service = NotificationService(mock_send)
        task = DownloadTask(
            task_id="test-1",
            url="https://youtube.com/watch?v=test",
            video_id="test",
            title="Test Video",
            quality="720p",
            status=TaskStatus.DOWNLOADING,
            notification_settings=NotificationSettings(
                notify_start=True,
                notify_progress=False,
                notify_completion=False,
                notify_errors=False
            )
        )
        
        await service.notify_download_start(task)
        
        assert len(messages) == 1
        assert "Загрузка начата" in messages[0]
        assert "Test Video" in messages[0]
        assert "720p" in messages[0]
        assert "test-1" in messages[0]
    
    @pytest.mark.asyncio
    async def test_notify_download_start_when_disabled(self):
        """Test that start notification is not sent when disabled"""
        messages = []
        
        async def mock_send(msg: str):
            messages.append(msg)
        
        service = NotificationService(mock_send)
        task = DownloadTask(
            task_id="test-1",
            url="https://youtube.com/watch?v=test",
            video_id="test",
            title="Test Video",
            quality="720p",
            status=TaskStatus.DOWNLOADING,
            notification_settings=NotificationSettings(
                notify_start=False,
                notify_progress=False,
                notify_completion=False,
                notify_errors=False
            )
        )
        
        await service.notify_download_start(task)
        
        assert len(messages) == 0
    
    @pytest.mark.asyncio
    async def test_notify_download_progress_when_enabled(self):
        """Test that progress notification is sent when enabled"""
        messages = []
        
        async def mock_send(msg: str):
            messages.append(msg)
        
        service = NotificationService(mock_send)
        task = DownloadTask(
            task_id="test-1",
            url="https://youtube.com/watch?v=test",
            video_id="test",
            title="Test Video",
            quality="720p",
            status=TaskStatus.DOWNLOADING,
            notification_settings=NotificationSettings(
                notify_start=False,
                notify_progress=True,
                notify_completion=False,
                notify_errors=False
            )
        )
        
        await service.notify_download_progress(task, 0.5)
        
        assert len(messages) == 1
        assert "Прогресс загрузки: 50%" in messages[0]
        assert "Test Video" in messages[0]
    
    @pytest.mark.asyncio
    async def test_notify_download_progress_when_disabled(self):
        """Test that progress notification is not sent when disabled"""
        messages = []
        
        async def mock_send(msg: str):
            messages.append(msg)
        
        service = NotificationService(mock_send)
        task = DownloadTask(
            task_id="test-1",
            url="https://youtube.com/watch?v=test",
            video_id="test",
            title="Test Video",
            quality="720p",
            status=TaskStatus.DOWNLOADING,
            notification_settings=NotificationSettings.no_notifications()
        )
        
        await service.notify_download_progress(task, 0.5)
        
        assert len(messages) == 0
    
    @pytest.mark.asyncio
    async def test_notify_download_complete_when_enabled(self):
        """Test that completion notification is sent when enabled"""
        messages = []
        
        async def mock_send(msg: str):
            messages.append(msg)
        
        service = NotificationService(mock_send)
        task = DownloadTask(
            task_id="test-1",
            url="https://youtube.com/watch?v=test",
            video_id="test",
            title="Test Video",
            quality="720p",
            status=TaskStatus.COMPLETED,
            file_size=10485760,  # 10 MB
            notification_settings=NotificationSettings(
                notify_start=False,
                notify_progress=False,
                notify_completion=True,
                notify_errors=False
            )
        )
        
        await service.notify_download_complete(task, "/videos/test.mp4")
        
        assert len(messages) == 1
        assert "Загрузка завершена" in messages[0]
        assert "Test Video" in messages[0]
        assert "/videos/test.mp4" in messages[0]
        assert "10.00 MB" in messages[0]
    
    @pytest.mark.asyncio
    async def test_notify_download_complete_when_disabled(self):
        """Test that completion notification is not sent when disabled"""
        messages = []
        
        async def mock_send(msg: str):
            messages.append(msg)
        
        service = NotificationService(mock_send)
        task = DownloadTask(
            task_id="test-1",
            url="https://youtube.com/watch?v=test",
            video_id="test",
            title="Test Video",
            quality="720p",
            status=TaskStatus.COMPLETED,
            notification_settings=NotificationSettings.no_notifications()
        )
        
        await service.notify_download_complete(task, "/videos/test.mp4")
        
        assert len(messages) == 0
    
    @pytest.mark.asyncio
    async def test_notify_download_error_when_enabled(self):
        """Test that error notification is sent when enabled"""
        messages = []
        
        async def mock_send(msg: str):
            messages.append(msg)
        
        service = NotificationService(mock_send)
        task = DownloadTask(
            task_id="test-1",
            url="https://youtube.com/watch?v=test",
            video_id="test",
            title="Test Video",
            quality="720p",
            status=TaskStatus.FAILED,
            notification_settings=NotificationSettings(
                notify_start=False,
                notify_progress=False,
                notify_completion=False,
                notify_errors=True
            )
        )
        
        await service.notify_download_error(task, "Network timeout")
        
        assert len(messages) == 1
        assert "Ошибка загрузки" in messages[0]
        assert "Test Video" in messages[0]
        assert "Network timeout" in messages[0]
    
    @pytest.mark.asyncio
    async def test_notify_download_error_when_disabled(self):
        """Test that error notification is not sent when disabled"""
        messages = []
        
        async def mock_send(msg: str):
            messages.append(msg)
        
        service = NotificationService(mock_send)
        task = DownloadTask(
            task_id="test-1",
            url="https://youtube.com/watch?v=test",
            video_id="test",
            title="Test Video",
            quality="720p",
            status=TaskStatus.FAILED,
            notification_settings=NotificationSettings.no_notifications()
        )
        
        await service.notify_download_error(task, "Network timeout")
        
        assert len(messages) == 0
    
    @pytest.mark.asyncio
    async def test_notify_storage_disconnected(self):
        """Test storage disconnection notification"""
        messages = []
        
        async def mock_send(msg: str):
            messages.append(msg)
        
        service = NotificationService(mock_send)
        
        await service.notify_storage_disconnected()
        
        assert len(messages) == 1
        assert "Хранилище недоступно" in messages[0]
        assert "приостановлены" in messages[0]
    
    @pytest.mark.asyncio
    async def test_notify_storage_full(self):
        """Test storage full notification"""
        messages = []
        
        async def mock_send(msg: str):
            messages.append(msg)
        
        service = NotificationService(mock_send)
        task = DownloadTask(
            task_id="test-1",
            url="https://youtube.com/watch?v=test",
            video_id="test",
            title="Test Video",
            quality="720p",
            status=TaskStatus.PAUSED,
            notification_settings=NotificationSettings.all_notifications()
        )
        
        await service.notify_storage_full(task)
        
        assert len(messages) == 1
        assert "Недостаточно места" in messages[0]
        assert "Test Video" in messages[0]
        assert "приостановлена" in messages[0]
    
    @pytest.mark.asyncio
    async def test_important_only_preset_behavior(self):
        """Test that important_only preset sends only start, completion, and errors"""
        messages = []
        
        async def mock_send(msg: str):
            messages.append(msg)
        
        service = NotificationService(mock_send)
        task = DownloadTask(
            task_id="test-1",
            url="https://youtube.com/watch?v=test",
            video_id="test",
            title="Test Video",
            quality="720p",
            status=TaskStatus.DOWNLOADING,
            notification_settings=NotificationSettings.important_only()
        )
        
        # Should send start notification
        await service.notify_download_start(task)
        assert len(messages) == 1
        
        # Should NOT send progress notification
        await service.notify_download_progress(task, 0.5)
        assert len(messages) == 1  # Still 1
        
        # Should send completion notification
        task.status = TaskStatus.COMPLETED
        await service.notify_download_complete(task, "/videos/test.mp4")
        assert len(messages) == 2
        
        # Should send error notification
        task.status = TaskStatus.FAILED
        await service.notify_download_error(task, "Test error")
        assert len(messages) == 3
