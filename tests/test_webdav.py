"""
Unit tests for WebDAV Service

Requirements: 2.1, 11.1, 11.2, 11.3, 11.4
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from hypothesis import given, strategies as st
from bot.webdav import WebDAVService, StorageInfo
from bot.database import WebDAVConfig
import base64


@pytest.mark.asyncio
async def test_connect_success():
    """Test successful connection to WebDAV storage"""
    service = WebDAVService()
    config = WebDAVConfig(
        url="https://webdav.example.com",
        username="testuser",
        password="testpass"
    )
    
    with patch('bot.webdav.httpx.AsyncClient') as mock_client_class, \
         patch('bot.webdav.Client') as mock_webdav_client:
        
        # Mock HTTP client
        mock_http_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 207
        mock_http_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_http_client
        
        # Mock WebDAV client
        mock_webdav_client.return_value = MagicMock()
        
        result = await service.connect(config)
        
        assert result is True
        assert service._config == config
        assert service._client is not None


@pytest.mark.asyncio
async def test_connect_failure():
    """Test connection failure to WebDAV storage"""
    service = WebDAVService()
    config = WebDAVConfig(
        url="https://webdav.example.com",
        username="testuser",
        password="wrongpass"
    )
    
    with patch('bot.webdav.httpx.AsyncClient') as mock_client_class, \
         patch('bot.webdav.Client') as mock_webdav_client:
        
        # Mock HTTP client - connection succeeds but test_connection fails
        mock_http_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 401  # Unauthorized
        mock_http_client.request = AsyncMock(return_value=mock_response)
        mock_http_client.aclose = AsyncMock()
        mock_client_class.return_value = mock_http_client
        
        # Mock WebDAV client
        mock_webdav_client.return_value = MagicMock()
        
        # Connection should return False (not raise exception)
        result = await service.connect(config)
        
        assert result is False
        # Client should be cleaned up on failure
        assert service._client is None
        assert service._config is None


@pytest.mark.asyncio
async def test_disconnect():
    """Test disconnection from WebDAV storage"""
    service = WebDAVService()
    
    # Mock connected state
    mock_http_client = AsyncMock()
    mock_http_client.aclose = AsyncMock()
    service._http_client = mock_http_client
    service._client = MagicMock()
    service._config = WebDAVConfig("url", "user", "pass")
    
    await service.disconnect()
    
    assert service._client is None
    assert service._config is None
    assert service._http_client is None
    mock_http_client.aclose.assert_called_once()


@pytest.mark.asyncio
async def test_test_connection_success():
    """Test connection test when connected"""
    service = WebDAVService()
    
    # Mock connected state
    mock_http_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 207
    mock_http_client.request = AsyncMock(return_value=mock_response)
    
    service._http_client = mock_http_client
    service._client = MagicMock()
    service._config = WebDAVConfig("https://webdav.example.com", "user", "pass")
    
    result = await service.test_connection()
    
    assert result is True


@pytest.mark.asyncio
async def test_test_connection_not_connected():
    """Test connection test when not connected"""
    service = WebDAVService()
    
    result = await service.test_connection()
    
    assert result is False


@pytest.mark.asyncio
async def test_get_storage_info_with_quota():
    """Test getting storage info with quota information"""
    service = WebDAVService()
    
    # Mock connected state
    mock_http_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 207
    mock_response.text = """<?xml version="1.0" encoding="utf-8"?>
    <D:multistatus xmlns:D="DAV:">
        <D:response>
            <D:propstat>
                <D:prop>
                    <D:quota-available-bytes>1000000000</D:quota-available-bytes>
                    <D:quota-used-bytes>500000000</D:quota-used-bytes>
                </D:prop>
            </D:propstat>
        </D:response>
    </D:multistatus>"""
    mock_http_client.request = AsyncMock(return_value=mock_response)
    
    service._http_client = mock_http_client
    service._client = MagicMock()
    service._config = WebDAVConfig("https://webdav.example.com", "user", "pass")
    
    info = await service.get_storage_info()
    
    assert info.is_connected is True
    assert info.free_space == 1000000000
    assert info.used_space == 500000000
    assert info.total_space == 1500000000


@pytest.mark.asyncio
async def test_get_storage_info_not_connected():
    """Test getting storage info when not connected"""
    service = WebDAVService()
    
    info = await service.get_storage_info()
    
    assert info.is_connected is False
    assert info.total_space == 0
    assert info.used_space == 0
    assert info.free_space == 0


@pytest.mark.asyncio
async def test_upload_file_success(tmp_path):
    """Test successful file upload"""
    service = WebDAVService()
    
    # Create test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    
    # Mock connected state
    mock_http_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_http_client.put = AsyncMock(return_value=mock_response)
    
    service._http_client = mock_http_client
    service._client = MagicMock()
    service._config = WebDAVConfig("https://webdav.example.com", "user", "pass")
    
    # Track progress callback
    progress_calls = []
    def progress_callback(uploaded, total):
        progress_calls.append((uploaded, total))
    
    result = await service.upload_file(
        str(test_file),
        "remote/test.txt",
        progress_callback
    )
    
    assert result is True
    assert len(progress_calls) > 0
    assert progress_calls[-1][0] == progress_calls[-1][1]  # Final progress should be 100%


@pytest.mark.asyncio
async def test_upload_file_not_connected(tmp_path):
    """Test file upload when not connected"""
    service = WebDAVService()
    
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    
    with pytest.raises(ConnectionError) as exc_info:
        await service.upload_file(str(test_file), "remote/test.txt")
    
    assert "Not connected to WebDAV storage" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_directory_success():
    """Test successful directory creation"""
    service = WebDAVService()
    
    # Mock connected state
    mock_http_client = AsyncMock()
    
    # Mock file_exists to return False (directory doesn't exist)
    service.file_exists = AsyncMock(return_value=False)
    
    # Mock MKCOL response
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_http_client.request = AsyncMock(return_value=mock_response)
    
    service._http_client = mock_http_client
    service._client = MagicMock()
    service._config = WebDAVConfig("https://webdav.example.com", "user", "pass")
    
    result = await service.create_directory("test_dir")
    
    assert result is True


@pytest.mark.asyncio
async def test_create_directory_already_exists():
    """Test directory creation when directory already exists"""
    service = WebDAVService()
    
    # Mock connected state
    mock_http_client = AsyncMock()
    service._http_client = mock_http_client
    service._client = MagicMock()
    service._config = WebDAVConfig("https://webdav.example.com", "user", "pass")
    
    # Mock file_exists to return True (directory exists)
    service.file_exists = AsyncMock(return_value=True)
    
    result = await service.create_directory("test_dir")
    
    assert result is True


@pytest.mark.asyncio
async def test_file_exists_true():
    """Test file existence check when file exists"""
    service = WebDAVService()
    
    # Mock connected state
    mock_http_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_http_client.head = AsyncMock(return_value=mock_response)
    
    service._http_client = mock_http_client
    service._client = MagicMock()
    service._config = WebDAVConfig("https://webdav.example.com", "user", "pass")
    
    result = await service.file_exists("test.txt")
    
    assert result is True


@pytest.mark.asyncio
async def test_file_exists_false():
    """Test file existence check when file doesn't exist"""
    service = WebDAVService()
    
    # Mock connected state
    mock_http_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_http_client.head = AsyncMock(return_value=mock_response)
    
    service._http_client = mock_http_client
    service._client = MagicMock()
    service._config = WebDAVConfig("https://webdav.example.com", "user", "pass")
    
    result = await service.file_exists("test.txt")
    
    assert result is False


def test_sanitize_filename_invalid_chars():
    """Test filename sanitization with invalid characters"""
    service = WebDAVService()
    
    # Test various invalid characters
    assert service.sanitize_filename("file/name.txt") == "file_name.txt"
    assert service.sanitize_filename("file\\name.txt") == "file_name.txt"
    assert service.sanitize_filename("file:name.txt") == "file_name.txt"
    assert service.sanitize_filename("file*name.txt") == "file_name.txt"
    assert service.sanitize_filename("file?name.txt") == "file_name.txt"
    assert service.sanitize_filename('file"name.txt') == "file_name.txt"
    assert service.sanitize_filename("file<name>.txt") == "file_name_.txt"
    assert service.sanitize_filename("file|name.txt") == "file_name.txt"


def test_sanitize_filename_leading_trailing():
    """Test filename sanitization with leading/trailing spaces and dots"""
    service = WebDAVService()
    
    assert service.sanitize_filename("  filename.txt  ") == "filename.txt"
    assert service.sanitize_filename("..filename.txt..") == "filename.txt"
    assert service.sanitize_filename(" . filename.txt . ") == "filename.txt"


def test_sanitize_filename_empty():
    """Test filename sanitization with empty or invalid input"""
    service = WebDAVService()
    
    assert service.sanitize_filename("") == "unnamed"
    assert service.sanitize_filename("   ") == "unnamed"
    assert service.sanitize_filename("...") == "unnamed"



# Property-Based Tests

# Feature: youtube-webdav-bot, Property 3: Использование Basic Auth для WebDAV
# **Validates: Requirements 2.2**
@given(
    url=st.text(min_size=10, max_size=100).map(lambda x: f"https://{x.replace('/', '')}.com"),
    username=st.text(min_size=3, max_size=50, alphabet=st.characters(blacklist_characters=[':'])),
    password=st.text(min_size=8, max_size=100)
)
@pytest.mark.asyncio
async def test_property_basic_auth_for_webdav(url, username, password):
    """
    Property 3: Использование Basic Auth для WebDAV
    
    Для любого запроса к WebDAV хранилищу, заголовки HTTP должны содержать
    корректную Basic Authentication с предоставленными учетными данными.
    
    Validates: Requirements 2.2
    """
    service = WebDAVService()
    config = WebDAVConfig(url=url, username=username, password=password)
    
    with patch('bot.webdav.httpx.AsyncClient') as mock_client_class, \
         patch('bot.webdav.Client') as mock_webdav_client:
        
        # Mock HTTP client
        mock_http_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 207
        mock_http_client.request = AsyncMock(return_value=mock_response)
        mock_http_client.aclose = AsyncMock()
        mock_client_class.return_value = mock_http_client
        
        # Mock WebDAV client
        mock_webdav_client.return_value = MagicMock()
        
        # Connect to WebDAV
        await service.connect(config)
        
        # Verify that AsyncClient was created with auth tuple
        mock_client_class.assert_called_once()
        call_kwargs = mock_client_class.call_args[1]
        
        # Check that auth parameter was passed
        assert 'auth' in call_kwargs, "Auth parameter must be present in HTTP client initialization"
        auth_tuple = call_kwargs['auth']
        
        # Verify auth tuple contains username and password
        assert auth_tuple == (username, password), \
            f"Auth tuple must contain correct credentials: expected ({username}, {password}), got {auth_tuple}"
        
        # Verify that WebDAV client was also created with auth
        mock_webdav_client.assert_called_once()
        webdav_call_kwargs = mock_webdav_client.call_args[1]
        assert 'auth' in webdav_call_kwargs, "Auth parameter must be present in WebDAV client initialization"
        webdav_auth_tuple = webdav_call_kwargs['auth']
        assert webdav_auth_tuple == (username, password), \
            f"WebDAV auth tuple must contain correct credentials: expected ({username}, {password}), got {webdav_auth_tuple}"
        
        # Clean up
        await service.disconnect()


# Feature: youtube-webdav-bot, Property 4: Описательные сообщения об ошибках подключения
# **Validates: Requirements 2.3**
@given(
    url=st.text(min_size=10, max_size=100).map(lambda x: f"https://{x.replace('/', '')}.com"),
    username=st.text(min_size=3, max_size=50),
    password=st.text(min_size=8, max_size=100)
)
@pytest.mark.asyncio
async def test_property_descriptive_error_messages(url, username, password):
    """
    Property 4: Описательные сообщения об ошибках подключения
    
    Для любой ошибки подключения к WebDAV хранилищу, система должна вернуть
    сообщение, содержащее описание причины ошибки.
    
    Validates: Requirements 2.3
    """
    service = WebDAVService()
    config = WebDAVConfig(url=url, username=username, password=password)
    
    with patch('bot.webdav.httpx.AsyncClient') as mock_client_class, \
         patch('bot.webdav.Client') as mock_webdav_client:
        
        # Simulate connection error
        error_message = "Connection timeout"
        mock_client_class.side_effect = Exception(error_message)
        
        # Attempt to connect should raise ConnectionError with descriptive message
        with pytest.raises(ConnectionError) as exc_info:
            await service.connect(config)
        
        # Verify error message contains description
        error_str = str(exc_info.value)
        assert "Failed to connect to WebDAV storage" in error_str, \
            "Error message must contain descriptive prefix"
        assert error_message in error_str, \
            f"Error message must contain original error: expected '{error_message}' in '{error_str}'"


# Feature: youtube-webdav-bot, Property 6: Единственное активное подключение к хранилищу
# **Validates: Requirements 2.5**
@given(
    url1=st.text(min_size=10, max_size=100).map(lambda x: f"https://{x.replace('/', '')}.com"),
    url2=st.text(min_size=10, max_size=100).map(lambda x: f"https://{x.replace('/', '')}.com"),
    username=st.text(min_size=3, max_size=50, alphabet=st.characters(blacklist_characters=[':'])),
    password=st.text(min_size=8, max_size=100)
)
@pytest.mark.asyncio
async def test_property_single_active_connection(url1, url2, username, password):
    """
    Property 6: Единственное активное подключение к хранилищу
    
    В любой момент времени, система должна поддерживать подключение только
    к одному WebDAV хранилищу.
    
    Validates: Requirements 2.5
    """
    service = WebDAVService()
    config1 = WebDAVConfig(url=url1, username=username, password=password)
    config2 = WebDAVConfig(url=url2, username=username, password=password)
    
    with patch('bot.webdav.httpx.AsyncClient') as mock_client_class, \
         patch('bot.webdav.Client') as mock_webdav_client:
        
        # Mock HTTP client
        mock_http_client1 = AsyncMock()
        mock_http_client2 = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 207
        mock_http_client1.request = AsyncMock(return_value=mock_response)
        mock_http_client2.request = AsyncMock(return_value=mock_response)
        mock_http_client1.aclose = AsyncMock()
        mock_http_client2.aclose = AsyncMock()
        
        # Return different clients for each call
        mock_client_class.side_effect = [mock_http_client1, mock_http_client2]
        
        # Mock WebDAV client
        mock_webdav_client.return_value = MagicMock()
        
        # Connect to first storage
        result1 = await service.connect(config1)
        assert result1 is True
        assert service._config == config1
        first_client = service._http_client
        
        # Connect to second storage - should disconnect from first
        result2 = await service.connect(config2)
        assert result2 is True
        assert service._config == config2
        
        # Verify first client was closed (disconnect was called)
        mock_http_client1.aclose.assert_called_once()
        
        # Verify only one connection is active
        assert service._http_client == mock_http_client2
        assert service._http_client != first_client
        
        # Clean up
        await service.disconnect()
