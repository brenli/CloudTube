"""
Unit tests for Download Service

Tests metadata extraction for videos and playlists.
Requirements: 3.1, 3.7, 4.1
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from bot.download import DownloadService, VideoMetadata


@pytest.fixture
def download_service():
    """Create a download service instance"""
    return DownloadService()


@pytest.fixture
def mock_video_info():
    """Mock video info from yt-dlp"""
    return {
        'id': 'dQw4w9WgXcQ',
        'title': 'Test Video',
        'duration': 212,
        'formats': [
            {
                'height': 1080,
                'vcodec': 'avc1',
                'filesize': 50000000,
            },
            {
                'height': 720,
                'vcodec': 'avc1',
                'filesize': 30000000,
            },
            {
                'height': 480,
                'vcodec': 'avc1',
                'filesize': 15000000,
            },
            {
                'height': 360,
                'vcodec': 'avc1',
                'filesize': 10000000,
            },
            # Audio-only format (should be skipped)
            {
                'vcodec': 'none',
                'acodec': 'opus',
                'filesize': 5000000,
            }
        ]
    }


@pytest.fixture
def mock_playlist_info():
    """Mock playlist info from yt-dlp"""
    return {
        'id': 'PLtest123',
        'title': 'Test Playlist',
        'entries': [
            {'id': 'video1'},
            {'id': 'video2'},
            {'id': 'video3'},
        ]
    }


@pytest.mark.asyncio
async def test_get_video_metadata_success(download_service, mock_video_info):
    """Test successful video metadata extraction"""
    with patch('yt_dlp.YoutubeDL') as mock_ydl_class:
        # Setup mock
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl.__exit__ = Mock(return_value=False)
        mock_ydl.extract_info = Mock(return_value=mock_video_info)
        mock_ydl_class.return_value = mock_ydl
        
        # Execute
        metadata = await download_service.get_video_metadata('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
        
        # Verify
        assert metadata.video_id == 'dQw4w9WgXcQ'
        assert metadata.title == 'Test Video'
        assert metadata.duration == 212
        assert 'best' in metadata.available_qualities
        assert '1080p' in metadata.available_qualities
        assert '720p' in metadata.available_qualities
        assert '480p' in metadata.available_qualities
        assert '360p' in metadata.available_qualities
        assert metadata.estimated_sizes['1080p'] == 50000000
        assert metadata.estimated_sizes['720p'] == 30000000


@pytest.mark.asyncio
async def test_get_video_metadata_invalid_url(download_service):
    """Test video metadata extraction with invalid URL"""
    with patch('yt_dlp.YoutubeDL') as mock_ydl_class:
        # Setup mock to raise DownloadError
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl.__exit__ = Mock(return_value=False)
        
        import yt_dlp
        mock_ydl.extract_info = Mock(side_effect=yt_dlp.utils.DownloadError("Video unavailable"))
        mock_ydl_class.return_value = mock_ydl
        
        # Execute and verify
        with pytest.raises(ValueError, match="Failed to extract video metadata"):
            await download_service.get_video_metadata('https://www.youtube.com/watch?v=invalid')


@pytest.mark.asyncio
async def test_get_video_metadata_no_video_id(download_service):
    """Test video metadata extraction when video ID is missing"""
    with patch('yt_dlp.YoutubeDL') as mock_ydl_class:
        # Setup mock with no video ID
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl.__exit__ = Mock(return_value=False)
        mock_ydl.extract_info = Mock(return_value={'title': 'Test'})
        mock_ydl_class.return_value = mock_ydl
        
        # Execute and verify
        with pytest.raises(ValueError, match="Could not extract video ID"):
            await download_service.get_video_metadata('https://www.youtube.com/watch?v=test')


@pytest.mark.asyncio
async def test_get_video_metadata_no_formats(download_service):
    """Test video metadata extraction with no formats available"""
    with patch('yt_dlp.YoutubeDL') as mock_ydl_class:
        # Setup mock with no formats
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl.__exit__ = Mock(return_value=False)
        mock_ydl.extract_info = Mock(return_value={
            'id': 'test123',
            'title': 'Test Video',
            'duration': 100,
            'formats': []
        })
        mock_ydl_class.return_value = mock_ydl
        
        # Execute
        metadata = await download_service.get_video_metadata('https://www.youtube.com/watch?v=test123')
        
        # Verify - should have at least 'best' quality
        assert metadata.video_id == 'test123'
        assert 'best' in metadata.available_qualities


@pytest.mark.asyncio
async def test_get_playlist_metadata_success(download_service, mock_playlist_info, mock_video_info):
    """Test successful playlist metadata extraction"""
    with patch('yt_dlp.YoutubeDL') as mock_ydl_class:
        # Setup mock
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl.__exit__ = Mock(return_value=False)
        
        # First call returns playlist info, subsequent calls return video info
        call_count = [0]
        def extract_info_side_effect(url, download=False):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_playlist_info
            else:
                # Return video info for each video
                return {**mock_video_info, 'id': f'video{call_count[0] - 1}'}
        
        mock_ydl.extract_info = Mock(side_effect=extract_info_side_effect)
        mock_ydl_class.return_value = mock_ydl
        
        # Execute
        metadata_list = await download_service.get_playlist_metadata('https://www.youtube.com/playlist?list=PLtest123')
        
        # Verify
        assert len(metadata_list) == 3
        assert all(isinstance(m, VideoMetadata) for m in metadata_list)


@pytest.mark.asyncio
async def test_get_playlist_metadata_invalid_url(download_service):
    """Test playlist metadata extraction with invalid URL"""
    with patch('yt_dlp.YoutubeDL') as mock_ydl_class:
        # Setup mock to raise DownloadError
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl.__exit__ = Mock(return_value=False)
        
        import yt_dlp
        mock_ydl.extract_info = Mock(side_effect=yt_dlp.utils.DownloadError("Playlist unavailable"))
        mock_ydl_class.return_value = mock_ydl
        
        # Execute and verify
        with pytest.raises(ValueError, match="Failed to extract playlist metadata"):
            await download_service.get_playlist_metadata('https://www.youtube.com/playlist?list=invalid')


@pytest.mark.asyncio
async def test_get_playlist_metadata_not_a_playlist(download_service, mock_video_info):
    """Test playlist metadata extraction with a video URL instead of playlist"""
    with patch('yt_dlp.YoutubeDL') as mock_ydl_class:
        # Setup mock to return video info (no 'entries' key)
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl.__exit__ = Mock(return_value=False)
        mock_ydl.extract_info = Mock(return_value=mock_video_info)
        mock_ydl_class.return_value = mock_ydl
        
        # Execute and verify
        with pytest.raises(ValueError, match="does not appear to be a playlist"):
            await download_service.get_playlist_metadata('https://www.youtube.com/watch?v=dQw4w9WgXcQ')


@pytest.mark.asyncio
async def test_get_playlist_metadata_empty_playlist(download_service):
    """Test playlist metadata extraction with empty playlist"""
    with patch('yt_dlp.YoutubeDL') as mock_ydl_class:
        # Setup mock with empty entries
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl.__exit__ = Mock(return_value=False)
        mock_ydl.extract_info = Mock(return_value={
            'id': 'PLtest123',
            'title': 'Empty Playlist',
            'entries': []
        })
        mock_ydl_class.return_value = mock_ydl
        
        # Execute and verify
        with pytest.raises(ValueError, match="Playlist is empty"):
            await download_service.get_playlist_metadata('https://www.youtube.com/playlist?list=PLtest123')


@pytest.mark.asyncio
async def test_get_playlist_metadata_with_unavailable_videos(download_service, mock_video_info):
    """Test playlist metadata extraction with some unavailable videos"""
    with patch('yt_dlp.YoutubeDL') as mock_ydl_class:
        # Setup mock
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl.__exit__ = Mock(return_value=False)
        
        # First call returns playlist with 3 videos
        playlist_info = {
            'id': 'PLtest123',
            'title': 'Test Playlist',
            'entries': [
                {'id': 'video1'},
                {'id': 'video2'},
                None,  # Unavailable video
            ]
        }
        
        call_count = [0]
        def extract_info_side_effect(url, download=False):
            call_count[0] += 1
            if call_count[0] == 1:
                return playlist_info
            else:
                # Return video info for valid videos
                return {**mock_video_info, 'id': f'video{call_count[0] - 1}'}
        
        mock_ydl.extract_info = Mock(side_effect=extract_info_side_effect)
        mock_ydl_class.return_value = mock_ydl
        
        # Execute
        metadata_list = await download_service.get_playlist_metadata('https://www.youtube.com/playlist?list=PLtest123')
        
        # Verify - should have 2 videos (skipped the unavailable one)
        assert len(metadata_list) == 2
