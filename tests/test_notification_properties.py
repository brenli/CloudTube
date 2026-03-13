"""
Property-based tests for Notification Service

Tests universal properties of notification behavior across many inputs.
Requirements: 6.3, 6.6
"""

import pytest
from hypothesis import given, strategies as st
from bot.notification import NotificationService
from bot.database import DownloadTask, NotificationSettings, TaskStatus


# Strategy for generating notification settings
@st.composite
def notification_settings_strategy(draw):
    """Generate arbitrary notification settings"""
    return NotificationSettings(
        notify_start=draw(st.booleans()),
        notify_progress=draw(st.booleans()),
        notify_completion=draw(st.booleans()),
        notify_errors=draw(st.booleans())
    )


# Strategy for generating download tasks
@st.composite
def download_task_strategy(draw, notification_settings=None):
    """Generate arbitrary download tasks"""
    if notification_settings is None:
        notification_settings = draw(notification_settings_strategy())
    
    return DownloadTask(
        task_id=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'))),
        url=draw(st.text(min_size=10, max_size=100)),
        video_id=draw(st.text(min_size=5, max_size=20)),
        title=draw(st.text(min_size=1, max_size=100)),
        quality=draw(st.sampled_from(['360p', '480p', '720p', '1080p', 'best'])),
        status=draw(st.sampled_from(list(TaskStatus))),
        progress=draw(st.floats(min_value=0.0, max_value=1.0)),
        file_size=draw(st.one_of(st.none(), st.integers(min_value=1, max_value=10**10))),
        notification_settings=notification_settings
    )


class TestNotificationProperties:
    """Property-based tests for notification service"""
    
    # Feature: youtube-webdav-bot, Property 23: Отправка только выбранных уведомлений
    @given(
        task=download_task_strategy(),
        progress=st.floats(min_value=0.0, max_value=1.0)
    )
    @pytest.mark.asyncio
    async def test_only_selected_notifications_are_sent(self, task, progress):
        """
        **Validates: Requirements 6.3**
        
        Для любой задачи загрузки с настройками уведомлений,
        система должна отправлять только те типы уведомлений,
        которые выбраны в настройках
        """
        messages = []
        
        async def mock_send(msg: str):
            messages.append(msg)
        
        service = NotificationService(mock_send)
        
        # Test start notification
        messages.clear()
        await service.notify_download_start(task)
        if task.notification_settings.notify_start:
            assert len(messages) == 1, "Start notification should be sent when enabled"
            assert "Загрузка начата" in messages[0]
        else:
            assert len(messages) == 0, "Start notification should not be sent when disabled"
        
        # Test progress notification
        messages.clear()
        await service.notify_download_progress(task, progress)
        if task.notification_settings.notify_progress:
            assert len(messages) == 1, "Progress notification should be sent when enabled"
            assert "Прогресс загрузки" in messages[0]
        else:
            assert len(messages) == 0, "Progress notification should not be sent when disabled"
        
        # Test completion notification
        messages.clear()
        await service.notify_download_complete(task, "/test/path.mp4")
        if task.notification_settings.notify_completion:
            assert len(messages) == 1, "Completion notification should be sent when enabled"
            assert "Загрузка завершена" in messages[0]
        else:
            assert len(messages) == 0, "Completion notification should not be sent when disabled"
        
        # Test error notification
        messages.clear()
        await service.notify_download_error(task, "Test error")
        if task.notification_settings.notify_errors:
            assert len(messages) == 1, "Error notification should be sent when enabled"
            assert "Ошибка загрузки" in messages[0]
        else:
            assert len(messages) == 0, "Error notification should not be sent when disabled"


    # Feature: youtube-webdav-bot, Property 24: Уведомления прогресса каждые 10%
    @given(
        task=download_task_strategy(notification_settings=NotificationSettings(
            notify_start=False,
            notify_progress=True,
            notify_completion=False,
            notify_errors=False
        )),
        progress_values=st.lists(
            st.floats(min_value=0.0, max_value=1.0),
            min_size=2,
            max_size=20
        ).map(sorted)  # Sort to simulate increasing progress
    )
    @pytest.mark.asyncio
    async def test_progress_notifications_every_10_percent(self, task, progress_values):
        """
        **Validates: Requirements 6.6**
        
        Для любой задачи с включенными уведомлениями прогресса,
        система должна отправлять уведомление при каждом достижении
        кратного 10% прогресса
        
        This test verifies that the notification service respects the 10% milestone
        pattern when the ProgressTracker (or similar component) calls it appropriately.
        """
        messages = []
        
        async def mock_send(msg: str):
            messages.append(msg)
        
        service = NotificationService(mock_send)
        
        # Simulate ProgressTracker behavior: only notify at 10% milestones
        # Track which 10% milestones we've crossed
        last_notified_milestone = -1
        
        for progress in progress_values:
            current_milestone = int(progress * 10)  # 0-10 (representing 0%, 10%, ..., 100%)
            
            # Only notify if we've crossed into a new 10% milestone
            if current_milestone > last_notified_milestone:
                # Notify for each milestone we crossed
                for milestone in range(last_notified_milestone + 1, current_milestone + 1):
                    milestone_progress = milestone / 10.0
                    await service.notify_download_progress(task, milestone_progress)
                
                last_notified_milestone = current_milestone
        
        # Verify we got notifications for each milestone crossed
        # The number of notifications should equal the highest milestone reached + 1
        # (since we start from milestone 0)
        highest_milestone = int(max(progress_values) * 10) if progress_values else 0
        expected_notifications = highest_milestone + 1
        
        assert len(messages) == expected_notifications, \
            f"Expected {expected_notifications} notifications for milestones 0-{highest_milestone}, got {len(messages)}"
        
        # Verify each notification contains progress information
        for msg in messages:
            assert "Прогресс загрузки" in msg
            assert "%" in msg
        
        # Verify notifications are in order and at 10% intervals
        for i, msg in enumerate(messages):
            expected_percent = i * 10
            assert f"{expected_percent}%" in msg, \
                f"Notification {i} should show {expected_percent}%, got: {msg}"
