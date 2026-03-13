"""
Unit tests for database layer

Requirements: 2.4, 3.6, 8.3
"""

import pytest
import os
import tempfile
from datetime import datetime, timezone
from bot.database import (
    Database, DownloadTask, WebDAVConfig, TaskStatus, NotificationSettings
)


@pytest.fixture
async def temp_db():
    """Create a temporary database for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = Database(db_path)
        await db.initialize()
        yield db
        await db.close()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_and_retrieve_task(temp_db):
    """Test creating and retrieving a download task"""
    task = DownloadTask(
        task_id="test-123",
        url="https://youtube.com/watch?v=test",
        video_id="test",
        title="Test Video",
        quality="720p",
        status=TaskStatus.PENDING,
        progress=0.0
    )
    
    await temp_db.save_task(task)
    retrieved = await temp_db.get_task("test-123")
    
    assert retrieved is not None
    assert retrieved.task_id == "test-123"
    assert retrieved.url == task.url
    assert retrieved.video_id == task.video_id
    assert retrieved.title == task.title
    assert retrieved.quality == task.quality
    assert retrieved.status == TaskStatus.PENDING
    assert retrieved.progress == 0.0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_task(temp_db):
    """Test updating a download task"""
    task = DownloadTask(
        task_id="test-456",
        url="https://youtube.com/watch?v=test",
        video_id="test",
        title="Test Video",
        quality="1080p",
        status=TaskStatus.PENDING
    )
    
    await temp_db.save_task(task)
    
    # Update task
    task.status = TaskStatus.DOWNLOADING
    task.progress = 0.5
    task.file_size = 1024000
    await temp_db.update_task(task)
    
    # Retrieve and verify
    retrieved = await temp_db.get_task("test-456")
    assert retrieved.status == TaskStatus.DOWNLOADING
    assert retrieved.progress == 0.5
    assert retrieved.file_size == 1024000


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_tasks_by_status(temp_db):
    """Test retrieving tasks by status"""
    # Create multiple tasks with different statuses
    tasks = [
        DownloadTask(
            task_id=f"task-{i}",
            url=f"https://youtube.com/watch?v={i}",
            video_id=f"vid-{i}",
            title=f"Video {i}",
            quality="720p",
            status=TaskStatus.PENDING if i % 2 == 0 else TaskStatus.COMPLETED
        )
        for i in range(5)
    ]
    
    for task in tasks:
        await temp_db.save_task(task)
    
    # Get pending tasks
    pending = await temp_db.get_tasks_by_status(TaskStatus.PENDING)
    assert len(pending) == 3  # tasks 0, 2, 4
    
    # Get completed tasks
    completed = await temp_db.get_tasks_by_status(TaskStatus.COMPLETED)
    assert len(completed) == 2  # tasks 1, 3


@pytest.mark.asyncio
@pytest.mark.unit
async def test_encrypt_decrypt_webdav_password(temp_db):
    """Test encryption and decryption of WebDAV passwords"""
    config = WebDAVConfig(
        url="https://webdav.example.com",
        username="testuser",
        password="super_secret_password_123"
    )
    
    await temp_db.save_webdav_config(config)
    retrieved = await temp_db.get_webdav_config()
    
    assert retrieved is not None
    assert retrieved.url == config.url
    assert retrieved.username == config.username
    assert retrieved.password == config.password  # Should be decrypted correctly


@pytest.mark.asyncio
@pytest.mark.unit
async def test_webdav_config_replacement(temp_db):
    """Test that saving WebDAV config replaces the existing one"""
    config1 = WebDAVConfig(
        url="https://webdav1.example.com",
        username="user1",
        password="password1"
    )
    
    config2 = WebDAVConfig(
        url="https://webdav2.example.com",
        username="user2",
        password="password2"
    )
    
    await temp_db.save_webdav_config(config1)
    await temp_db.save_webdav_config(config2)
    
    retrieved = await temp_db.get_webdav_config()
    assert retrieved.url == config2.url
    assert retrieved.username == config2.username
    assert retrieved.password == config2.password


@pytest.mark.asyncio
@pytest.mark.unit
async def test_notification_settings_persistence(temp_db):
    """Test that notification settings are persisted correctly"""
    task = DownloadTask(
        task_id="test-notif",
        url="https://youtube.com/watch?v=test",
        video_id="test",
        title="Test Video",
        quality="720p",
        status=TaskStatus.PENDING,
        notification_settings=NotificationSettings.errors_only()
    )
    
    await temp_db.save_task(task)
    retrieved = await temp_db.get_task("test-notif")
    
    assert retrieved.notification_settings.notify_start is False
    assert retrieved.notification_settings.notify_progress is False
    assert retrieved.notification_settings.notify_completion is False
    assert retrieved.notification_settings.notify_errors is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_all_tasks(temp_db):
    """Test retrieving all tasks"""
    tasks = [
        DownloadTask(
            task_id=f"task-{i}",
            url=f"https://youtube.com/watch?v={i}",
            video_id=f"vid-{i}",
            title=f"Video {i}",
            quality="720p",
            status=TaskStatus.PENDING
        )
        for i in range(3)
    ]
    
    for task in tasks:
        await temp_db.save_task(task)
    
    all_tasks = await temp_db.get_all_tasks()
    assert len(all_tasks) == 3


@pytest.mark.asyncio
@pytest.mark.unit
async def test_task_not_found(temp_db):
    """Test retrieving a non-existent task returns None"""
    result = await temp_db.get_task("non-existent")
    assert result is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_webdav_config_not_found(temp_db):
    """Test retrieving WebDAV config when none exists returns None"""
    result = await temp_db.get_webdav_config()
    assert result is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_task_timestamps(temp_db):
    """Test that task timestamps are set correctly"""
    task = DownloadTask(
        task_id="test-time",
        url="https://youtube.com/watch?v=test",
        video_id="test",
        title="Test Video",
        quality="720p",
        status=TaskStatus.PENDING
    )
    
    before = datetime.now(timezone.utc)
    await temp_db.save_task(task)
    after = datetime.now(timezone.utc)
    
    retrieved = await temp_db.get_task("test-time")
    assert before <= retrieved.created_at <= after
    assert before <= retrieved.updated_at <= after


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_task_updates_timestamp(temp_db):
    """Test that updating a task updates the updated_at timestamp"""
    task = DownloadTask(
        task_id="test-update-time",
        url="https://youtube.com/watch?v=test",
        video_id="test",
        title="Test Video",
        quality="720p",
        status=TaskStatus.PENDING
    )
    
    await temp_db.save_task(task)
    original = await temp_db.get_task("test-update-time")
    
    # Wait a bit and update
    import asyncio
    await asyncio.sleep(0.01)
    
    task.status = TaskStatus.DOWNLOADING
    await temp_db.update_task(task)
    
    updated = await temp_db.get_task("test-update-time")
    assert updated.updated_at > original.updated_at



# Property-based tests
from hypothesis import given, strategies as st, assume, settings


def valid_task_id():
    """Strategy for valid task IDs"""
    return st.text(min_size=1, max_size=100, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='-_'
    ))


def valid_url():
    """Strategy for valid URLs"""
    return st.text(min_size=10, max_size=200, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters=':/.-_?=&'
    ))


def valid_text():
    """Strategy for valid text fields"""
    return st.text(min_size=1, max_size=200)


def valid_quality():
    """Strategy for valid quality values"""
    return st.sampled_from(["best", "1080p", "720p", "480p", "360p"])


@pytest.mark.asyncio
@pytest.mark.property
@settings(deadline=None)
@given(
    task_id=valid_task_id(),
    url=valid_url(),
    video_id=valid_task_id(),
    title=valid_text(),
    quality=valid_quality(),
    status=st.sampled_from(list(TaskStatus)),
    progress=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    file_size=st.one_of(st.none(), st.integers(min_value=0, max_value=10**10)),
    remote_path=st.one_of(st.none(), valid_text()),
    error_message=st.one_of(st.none(), valid_text()),
    notify_start=st.booleans(),
    notify_progress=st.booleans(),
    notify_completion=st.booleans(),
    notify_errors=st.booleans(),
)
async def test_property_5_task_round_trip_persistence(
    task_id, url, video_id, title, quality, status, progress,
    file_size, remote_path, error_message,
    notify_start, notify_progress, notify_completion, notify_errors
):
    """
    Property 5: Round-trip персистентности данных
    
    Для любых данных (задачи загрузки), сохранение в БД и последующая
    загрузка должны возвращать эквивалентные данные
    
    Validates: Requirements 2.4, 6.7, 8.4
    """
    # Create temporary database
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = Database(db_path)
        await db.initialize()
        
        try:
            # Create task with generated data
            original_task = DownloadTask(
                task_id=task_id,
                url=url,
                video_id=video_id,
                title=title,
                quality=quality,
                status=status,
                progress=progress,
                file_size=file_size,
                remote_path=remote_path,
                error_message=error_message,
                notification_settings=NotificationSettings(
                    notify_start=notify_start,
                    notify_progress=notify_progress,
                    notify_completion=notify_completion,
                    notify_errors=notify_errors
                )
            )
            
            # Save to database
            await db.save_task(original_task)
            
            # Retrieve from database
            retrieved_task = await db.get_task(task_id)
            
            # Verify round-trip: all fields should match
            assert retrieved_task is not None, "Task should be retrievable after saving"
            assert retrieved_task.task_id == original_task.task_id
            assert retrieved_task.url == original_task.url
            assert retrieved_task.video_id == original_task.video_id
            assert retrieved_task.title == original_task.title
            assert retrieved_task.quality == original_task.quality
            assert retrieved_task.status == original_task.status
            assert abs(retrieved_task.progress - original_task.progress) < 0.0001
            assert retrieved_task.file_size == original_task.file_size
            assert retrieved_task.remote_path == original_task.remote_path
            assert retrieved_task.error_message == original_task.error_message
            
            # Verify notification settings
            assert retrieved_task.notification_settings.notify_start == original_task.notification_settings.notify_start
            assert retrieved_task.notification_settings.notify_progress == original_task.notification_settings.notify_progress
            assert retrieved_task.notification_settings.notify_completion == original_task.notification_settings.notify_completion
            assert retrieved_task.notification_settings.notify_errors == original_task.notification_settings.notify_errors
            
            # Timestamps should be preserved (within reasonable tolerance)
            assert retrieved_task.created_at == original_task.created_at
            assert retrieved_task.updated_at == original_task.updated_at
            
        finally:
            await db.close()


@pytest.mark.asyncio
@pytest.mark.property
@settings(deadline=None)
@given(
    url=valid_url(),
    username=valid_text(),
    password=st.text(min_size=8, max_size=100),
)
async def test_property_5_webdav_config_round_trip_persistence(url, username, password):
    """
    Property 5: Round-trip персистентности данных (WebDAV config)
    
    Для любых данных (конфигурация WebDAV), сохранение в БД и последующая
    загрузка должны возвращать эквивалентные данные
    
    Validates: Requirements 2.4, 6.7, 8.4
    """
    # Create temporary database
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = Database(db_path)
        await db.initialize()
        
        try:
            # Create WebDAV config with generated data
            original_config = WebDAVConfig(
                url=url,
                username=username,
                password=password
            )
            
            # Save to database
            await db.save_webdav_config(original_config)
            
            # Retrieve from database
            retrieved_config = await db.get_webdav_config()
            
            # Verify round-trip: all fields should match
            assert retrieved_config is not None, "Config should be retrievable after saving"
            assert retrieved_config.url == original_config.url
            assert retrieved_config.username == original_config.username
            # Password should be decrypted correctly
            assert retrieved_config.password == original_config.password
            
        finally:
            await db.close()


@pytest.mark.asyncio
@pytest.mark.property
@settings(deadline=None)
@given(
    task_id=valid_task_id(),
    url=valid_url(),
    video_id=valid_task_id(),
    title=valid_text(),
    quality=valid_quality(),
    initial_status=st.sampled_from(list(TaskStatus)),
    updated_status=st.sampled_from(list(TaskStatus)),
    initial_progress=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    updated_progress=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
)
async def test_property_5_task_update_persistence(
    task_id, url, video_id, title, quality,
    initial_status, updated_status, initial_progress, updated_progress
):
    """
    Property 5: Round-trip персистентности данных (task updates)
    
    Для любых обновлений задачи, сохранение и загрузка должны
    возвращать обновленные данные
    
    Validates: Requirements 2.4, 6.7, 8.4
    """
    # Create temporary database
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = Database(db_path)
        await db.initialize()
        
        try:
            # Create and save initial task
            task = DownloadTask(
                task_id=task_id,
                url=url,
                video_id=video_id,
                title=title,
                quality=quality,
                status=initial_status,
                progress=initial_progress
            )
            
            await db.save_task(task)
            
            # Update task
            task.status = updated_status
            task.progress = updated_progress
            await db.update_task(task)
            
            # Retrieve and verify updates persisted
            retrieved = await db.get_task(task_id)
            
            assert retrieved is not None
            assert retrieved.status == updated_status
            assert abs(retrieved.progress - updated_progress) < 0.0001
            
        finally:
            await db.close()
