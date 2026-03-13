"""
Property-based tests for Download Service

Tests universal properties of metadata extraction across many inputs.
Requirements: 3.1, 3.2, 4.1, 4.2
"""

import pytest
from hypothesis import given, strategies as st, assume
from unittest.mock import Mock, patch, MagicMock
from bot.download import DownloadService, VideoMetadata


# Strategy for generating valid video IDs
video_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'),
    min_size=5,
    max_size=20
)

# Strategy for generating video titles
title_strategy = st.text(min_size=1, max_size=100)

# Strategy for generating durations (in seconds)
duration_strategy = st.integers(min_value=1, max_value=86400)  # 1 second to 24 hours

# Strategy for generating file sizes
filesize_strategy = st.integers(min_value=1000000, max_value=5000000000)  # 1MB to 5GB


def create_mock_video_info(video_id: str, title: str, duration: int, formats: list) -> dict:
    """Helper to create mock video info"""
    return {
        'id': video_id,
        'title': title,
        'duration': duration,
        'formats': formats
    }


def create_mock_format(height: int, filesize: int) -> dict:
    """Helper to create mock format"""
    return {
        'height': height,
        'vcodec': 'avc1',
        'filesize': filesize
    }


# Feature: youtube-webdav-bot, Property 9: Извлечение метаданных видео
@given(
    video_id=video_id_strategy,
    title=title_strategy,
    duration=duration_strategy,
    filesize_1080=filesize_strategy,
    filesize_720=filesize_strategy,
    filesize_480=filesize_strategy,
)
@pytest.mark.asyncio
async def test_property_9_extract_video_metadata(
    video_id, title, duration, filesize_1080, filesize_720, filesize_480
):
    """
    Property 9: Извлечение метаданных видео
    
    Для любого валидного URL видео YouTube, система должна извлечь метаданные,
    включающие название, длительность, доступные качества и размеры
    
    **Validates: Requirements 3.1**
    """
    # Arrange
    service = DownloadService()
    
    formats = [
        create_mock_format(1080, filesize_1080),
        create_mock_format(720, filesize_720),
        create_mock_format(480, filesize_480),
    ]
    
    mock_info = create_mock_video_info(video_id, title, duration, formats)
    
    with patch('yt_dlp.YoutubeDL') as mock_ydl_class:
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl.__exit__ = Mock(return_value=False)
        mock_ydl.extract_info = Mock(return_value=mock_info)
        mock_ydl_class.return_value = mock_ydl
        
        # Act
        metadata = await service.get_video_metadata(f'https://www.youtube.com/watch?v={video_id}')
        
        # Assert - metadata must include all required fields
        assert metadata.video_id == video_id
        assert metadata.title == title
        assert metadata.duration == duration
        assert len(metadata.available_qualities) > 0
        assert len(metadata.estimated_sizes) > 0


# Feature: youtube-webdav-bot, Property 10: Отображение метаданных с размерами
@given(
    video_id=video_id_strategy,
    title=title_strategy,
    duration=duration_strategy,
    filesize_1080=filesize_strategy,
    filesize_720=filesize_strategy,
)
@pytest.mark.asyncio
async def test_property_10_display_metadata_with_sizes(
    video_id, title, duration, filesize_1080, filesize_720
):
    """
    Property 10: Отображение метаданных с размерами
    
    Для любых извлеченных метаданных видео, отображаемая информация должна
    содержать список качеств и примерный размер файла для каждого качества
    
    **Validates: Requirements 3.2**
    """
    # Arrange
    service = DownloadService()
    
    formats = [
        create_mock_format(1080, filesize_1080),
        create_mock_format(720, filesize_720),
    ]
    
    mock_info = create_mock_video_info(video_id, title, duration, formats)
    
    with patch('yt_dlp.YoutubeDL') as mock_ydl_class:
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl.__exit__ = Mock(return_value=False)
        mock_ydl.extract_info = Mock(return_value=mock_info)
        mock_ydl_class.return_value = mock_ydl
        
        # Act
        metadata = await service.get_video_metadata(f'https://www.youtube.com/watch?v={video_id}')
        
        # Assert - each quality must have an estimated size
        for quality in metadata.available_qualities:
            assert quality in metadata.estimated_sizes
            assert metadata.estimated_sizes[quality] > 0


# Feature: youtube-webdav-bot, Property 15: Извлечение метаданных плейлиста
@given(
    playlist_id=st.text(min_size=10, max_size=30),
    num_videos=st.integers(min_value=1, max_value=5),  # Keep small for test performance
)
@pytest.mark.asyncio
async def test_property_15_extract_playlist_metadata(playlist_id, num_videos):
    """
    Property 15: Извлечение метаданных плейлиста
    
    Для любого валидного URL плейлиста YouTube, система должна извлечь
    список всех видео с их метаданными
    
    **Validates: Requirements 4.1**
    """
    # Arrange
    service = DownloadService()
    
    # Create mock playlist with N videos
    entries = [{'id': f'video{i}'} for i in range(num_videos)]
    
    playlist_info = {
        'id': playlist_id,
        'title': 'Test Playlist',
        'entries': entries
    }
    
    # Create mock video info
    mock_video_info = create_mock_video_info(
        'test_video',
        'Test Video',
        100,
        [create_mock_format(720, 10000000)]
    )
    
    with patch('yt_dlp.YoutubeDL') as mock_ydl_class:
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl.__exit__ = Mock(return_value=False)
        
        call_count = [0]
        def extract_info_side_effect(url, download=False):
            call_count[0] += 1
            if call_count[0] == 1:
                return playlist_info
            else:
                return {**mock_video_info, 'id': f'video{call_count[0] - 1}'}
        
        mock_ydl.extract_info = Mock(side_effect=extract_info_side_effect)
        mock_ydl_class.return_value = mock_ydl
        
        # Act
        metadata_list = await service.get_playlist_metadata(f'https://www.youtube.com/playlist?list={playlist_id}')
        
        # Assert - must extract metadata for all videos
        assert len(metadata_list) == num_videos
        assert all(isinstance(m, VideoMetadata) for m in metadata_list)


# Feature: youtube-webdav-bot, Property 16: Отображение суммарной информации о плейлисте
@given(
    playlist_id=st.text(min_size=10, max_size=30),
    num_videos=st.integers(min_value=1, max_value=5),
    video_sizes=st.lists(
        st.integers(min_value=1000000, max_value=100000000),
        min_size=1,
        max_size=5
    )
)
@pytest.mark.asyncio
async def test_property_16_display_playlist_summary(playlist_id, num_videos, video_sizes):
    """
    Property 16: Отображение суммарной информации о плейлисте
    
    Для любого обрабатываемого плейлиста, отображаемая информация должна
    содержать общее количество видео и суммарный примерный размер
    
    **Validates: Requirements 4.2**
    """
    # Ensure we have enough sizes for the videos
    assume(len(video_sizes) >= num_videos)
    
    # Arrange
    service = DownloadService()
    
    # Create mock playlist with N videos
    entries = [{'id': f'video{i}'} for i in range(num_videos)]
    
    playlist_info = {
        'id': playlist_id,
        'title': 'Test Playlist',
        'entries': entries
    }
    
    with patch('yt_dlp.YoutubeDL') as mock_ydl_class:
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl.__exit__ = Mock(return_value=False)
        
        call_count = [0]
        def extract_info_side_effect(url, download=False):
            call_count[0] += 1
            if call_count[0] == 1:
                return playlist_info
            else:
                video_idx = call_count[0] - 2
                size = video_sizes[video_idx] if video_idx < len(video_sizes) else video_sizes[0]
                return create_mock_video_info(
                    f'video{video_idx}',
                    f'Video {video_idx}',
                    100,
                    [create_mock_format(720, size)]
                )
        
        mock_ydl.extract_info = Mock(side_effect=extract_info_side_effect)
        mock_ydl_class.return_value = mock_ydl
        
        # Act
        metadata_list = await service.get_playlist_metadata(f'https://www.youtube.com/playlist?list={playlist_id}')
        
        # Assert - can calculate total count and size
        total_count = len(metadata_list)
        total_size = sum(
            max(m.estimated_sizes.values()) if m.estimated_sizes else 0
            for m in metadata_list
        )
        
        assert total_count == num_videos
        assert total_size > 0  # Total size should be positive
