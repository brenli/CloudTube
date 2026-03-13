"""
Configuration management for the bot
"""

import os
from dataclasses import dataclass


@dataclass
class AppConfig:
    """Application configuration"""
    telegram_token: str
    owner_id: int
    database_path: str
    temp_download_path: str
    log_level: str
    log_path: str
    max_concurrent_downloads: int


class ConfigManager:
    """Manages application configuration"""
    
    @staticmethod
    def load_from_env() -> AppConfig:
        """Load configuration from environment variables"""
        return AppConfig(
            telegram_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            owner_id=int(os.getenv("TELEGRAM_OWNER_ID", "0")),
            database_path=os.getenv("DATABASE_PATH", "./data/bot.db"),
            temp_download_path=os.getenv("TEMP_DOWNLOAD_PATH", "./temp"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_path=os.getenv("LOG_PATH", "./logs"),
            max_concurrent_downloads=int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "2")),
        )
    
    @staticmethod
    def validate_config(config: AppConfig) -> list[str]:
        """
        Validate configuration and return list of errors
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        if not config.telegram_token:
            errors.append("TELEGRAM_BOT_TOKEN is required")
        
        if config.owner_id == 0:
            errors.append("TELEGRAM_OWNER_ID is required and must be a valid Telegram user ID")
        
        if not config.database_path:
            errors.append("DATABASE_PATH is required")
        
        if not config.temp_download_path:
            errors.append("TEMP_DOWNLOAD_PATH is required")
        
        if config.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            errors.append(f"LOG_LEVEL must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL (got: {config.log_level})")
        
        if config.max_concurrent_downloads < 1:
            errors.append("MAX_CONCURRENT_DOWNLOADS must be at least 1")
        
        return errors
