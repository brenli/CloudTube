"""
Unit tests for configuration management

Requirements: 14.1, 14.2
"""

import os
import pytest
from bot.config import AppConfig, ConfigManager


@pytest.mark.unit
def test_load_config_with_all_parameters(monkeypatch):
    """Test successful loading of all configuration parameters"""
    # Set all environment variables
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token_123")
    monkeypatch.setenv("TELEGRAM_OWNER_ID", "12345678")
    monkeypatch.setenv("DATABASE_PATH", "/custom/path/bot.db")
    monkeypatch.setenv("TEMP_DOWNLOAD_PATH", "/custom/temp")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("LOG_PATH", "/custom/logs")
    monkeypatch.setenv("MAX_CONCURRENT_DOWNLOADS", "3")
    
    config = ConfigManager.load_from_env()
    
    assert config.telegram_token == "test_token_123"
    assert config.owner_id == 12345678
    assert config.database_path == "/custom/path/bot.db"
    assert config.temp_download_path == "/custom/temp"
    assert config.log_level == "DEBUG"
    assert config.log_path == "/custom/logs"
    assert config.max_concurrent_downloads == 3


@pytest.mark.unit
def test_load_config_with_defaults(monkeypatch):
    """Test loading configuration with default values when optional params are missing"""
    # Set only required parameters
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
    monkeypatch.setenv("TELEGRAM_OWNER_ID", "12345678")
    
    # Clear optional parameters
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    monkeypatch.delenv("TEMP_DOWNLOAD_PATH", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("LOG_PATH", raising=False)
    monkeypatch.delenv("MAX_CONCURRENT_DOWNLOADS", raising=False)
    
    config = ConfigManager.load_from_env()
    
    # Check defaults
    assert config.database_path == "./data/bot.db"
    assert config.temp_download_path == "./temp"
    assert config.log_level == "INFO"
    assert config.log_path == "./logs"
    assert config.max_concurrent_downloads == 2


@pytest.mark.unit
def test_validate_config_missing_telegram_token(monkeypatch):
    """Test validation fails when TELEGRAM_BOT_TOKEN is missing"""
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("TELEGRAM_OWNER_ID", "12345678")
    
    config = ConfigManager.load_from_env()
    errors = ConfigManager.validate_config(config)
    
    assert len(errors) > 0
    assert any("TELEGRAM_BOT_TOKEN" in error for error in errors)


@pytest.mark.unit
def test_validate_config_missing_owner_id(monkeypatch):
    """Test validation fails when TELEGRAM_OWNER_ID is missing or zero"""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
    monkeypatch.delenv("TELEGRAM_OWNER_ID", raising=False)
    
    config = ConfigManager.load_from_env()
    errors = ConfigManager.validate_config(config)
    
    assert len(errors) > 0
    assert any("TELEGRAM_OWNER_ID" in error for error in errors)


@pytest.mark.unit
def test_validate_config_invalid_log_level(monkeypatch):
    """Test validation fails with invalid log level"""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
    monkeypatch.setenv("TELEGRAM_OWNER_ID", "12345678")
    monkeypatch.setenv("LOG_LEVEL", "INVALID")
    
    config = ConfigManager.load_from_env()
    errors = ConfigManager.validate_config(config)
    
    assert len(errors) > 0
    assert any("LOG_LEVEL" in error for error in errors)


@pytest.mark.unit
def test_validate_config_invalid_max_concurrent_downloads(monkeypatch):
    """Test validation fails when MAX_CONCURRENT_DOWNLOADS is less than 1"""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
    monkeypatch.setenv("TELEGRAM_OWNER_ID", "12345678")
    monkeypatch.setenv("MAX_CONCURRENT_DOWNLOADS", "0")
    
    config = ConfigManager.load_from_env()
    errors = ConfigManager.validate_config(config)
    
    assert len(errors) > 0
    assert any("MAX_CONCURRENT_DOWNLOADS" in error for error in errors)


@pytest.mark.unit
def test_validate_config_all_valid(monkeypatch):
    """Test validation passes with all valid parameters"""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token_123")
    monkeypatch.setenv("TELEGRAM_OWNER_ID", "12345678")
    monkeypatch.setenv("DATABASE_PATH", "/path/to/db")
    monkeypatch.setenv("TEMP_DOWNLOAD_PATH", "/path/to/temp")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("LOG_PATH", "/path/to/logs")
    monkeypatch.setenv("MAX_CONCURRENT_DOWNLOADS", "2")
    
    config = ConfigManager.load_from_env()
    errors = ConfigManager.validate_config(config)
    
    assert len(errors) == 0


@pytest.mark.unit
def test_validate_config_multiple_errors(monkeypatch):
    """Test validation returns multiple errors when multiple parameters are invalid"""
    # Clear all environment variables
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_OWNER_ID", raising=False)
    monkeypatch.setenv("LOG_LEVEL", "INVALID")
    monkeypatch.setenv("MAX_CONCURRENT_DOWNLOADS", "-1")
    
    config = ConfigManager.load_from_env()
    errors = ConfigManager.validate_config(config)
    
    # Should have multiple errors
    assert len(errors) >= 3
    assert any("TELEGRAM_BOT_TOKEN" in error for error in errors)
    assert any("TELEGRAM_OWNER_ID" in error for error in errors)
    assert any("LOG_LEVEL" in error for error in errors)


# Property-based tests
from hypothesis import given, strategies as st


@pytest.mark.property
@given(
    telegram_token=st.one_of(st.just(""), st.none()),
    owner_id=st.one_of(st.just(0), st.integers(min_value=-1000, max_value=0)),
    database_path=st.one_of(st.just(""), st.none()),
    temp_download_path=st.one_of(st.just(""), st.none()),
)
def test_property_46_validate_required_parameters(
    telegram_token, owner_id, database_path, temp_download_path
):
    """
    Property 46: Валидация обязательных параметров конфигурации
    
    Для любого обязательного параметра конфигурации (токен бота, путь к БД),
    если он отсутствует, бот должен вывести описательное сообщение об ошибке
    
    Validates: Requirements 14.2, 14.3
    """
    # Create config with potentially invalid required parameters
    config = AppConfig(
        telegram_token=telegram_token if telegram_token is not None else "",
        owner_id=owner_id,
        database_path=database_path if database_path is not None else "",
        temp_download_path=temp_download_path if temp_download_path is not None else "",
        log_level="INFO",
        log_path="./logs",
        max_concurrent_downloads=2,
    )
    
    errors = ConfigManager.validate_config(config)
    
    # At least one error should be present since we're testing invalid configs
    assert len(errors) > 0, "Validation should fail for missing required parameters"
    
    # Each error should be descriptive (contain the parameter name)
    for error in errors:
        assert isinstance(error, str), "Error messages should be strings"
        assert len(error) > 10, "Error messages should be descriptive"
        
        # Check that error messages mention the problematic parameter
        if not telegram_token:
            if "TELEGRAM_BOT_TOKEN" in error:
                assert "required" in error.lower() or "missing" in error.lower()
        
        if owner_id <= 0:
            if "TELEGRAM_OWNER_ID" in error or "owner_id" in error.lower():
                assert "required" in error.lower() or "valid" in error.lower()
        
        if not database_path:
            if "DATABASE_PATH" in error:
                assert "required" in error.lower()
        
        if not temp_download_path:
            if "TEMP_DOWNLOAD_PATH" in error:
                assert "required" in error.lower()


@pytest.mark.property
@given(
    telegram_token=st.text(min_size=10, max_size=100),
    owner_id=st.integers(min_value=1, max_value=999999999),
    database_path=st.text(min_size=5, max_size=100),
    temp_download_path=st.text(min_size=5, max_size=100),
    log_level=st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    log_path=st.text(min_size=1, max_size=100),
    max_concurrent_downloads=st.integers(min_value=1, max_value=10),
)
def test_property_46_valid_config_has_no_errors(
    telegram_token, owner_id, database_path, temp_download_path,
    log_level, log_path, max_concurrent_downloads
):
    """
    Property 46 (complement): Valid configuration should have no errors
    
    For any valid configuration with all required parameters present,
    validation should return no errors
    
    Validates: Requirements 14.2, 14.3
    """
    config = AppConfig(
        telegram_token=telegram_token,
        owner_id=owner_id,
        database_path=database_path,
        temp_download_path=temp_download_path,
        log_level=log_level,
        log_path=log_path,
        max_concurrent_downloads=max_concurrent_downloads,
    )
    
    errors = ConfigManager.validate_config(config)
    
    # Valid configuration should have no errors
    assert len(errors) == 0, f"Valid configuration should have no errors, but got: {errors}"
