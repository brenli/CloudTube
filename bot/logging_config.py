"""
Logging configuration

Provides centralized logging setup with rotation and retention policies.

Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6
"""

import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime, timedelta


def setup_logging(log_dir: str = "logs", log_level: str = "INFO") -> None:
    """
    Setup logging with rotation and retention
    
    Args:
        log_dir: Directory for log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6
    """
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation (10MB max, keep 30 days)
    log_file = log_path / "bot.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=30,  # Keep 30 backup files
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Cleanup old log files (older than 30 days)
    cleanup_old_logs(log_path, days=30)
    
    logger.info("Logging initialized")


def cleanup_old_logs(log_dir: Path, days: int = 30) -> None:
    """
    Remove log files older than specified days
    
    Args:
        log_dir: Directory containing log files
        days: Number of days to retain logs
        
    Requirements: 13.6
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    
    for log_file in log_dir.glob("*.log*"):
        try:
            # Get file modification time
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            
            # Delete if older than cutoff
            if mtime < cutoff_date:
                log_file.unlink()
                logging.info(f"Deleted old log file: {log_file}")
        except Exception as e:
            logging.error(f"Error deleting log file {log_file}: {e}")


def log_access_attempt(user_id: int, username: str, authorized: bool) -> None:
    """
    Log access attempt
    
    Args:
        user_id: Telegram user ID
        username: Telegram username
        authorized: Whether access was authorized
        
    Requirements: 13.2
    """
    logger = logging.getLogger("bot.auth")
    
    if authorized:
        logger.info(f"Authorized access: user_id={user_id}, username={username}")
    else:
        logger.warning(f"Unauthorized access attempt: user_id={user_id}, username={username}")


def log_download_start(task_id: str, url: str, quality: str) -> None:
    """
    Log download task start
    
    Args:
        task_id: Task ID
        url: Video URL
        quality: Selected quality
        
    Requirements: 13.3
    """
    logger = logging.getLogger("bot.download")
    logger.info(f"Download started: task_id={task_id}, url={url}, quality={quality}")


def log_download_complete(task_id: str, title: str, remote_path: str) -> None:
    """
    Log download task completion
    
    Args:
        task_id: Task ID
        title: Video title
        remote_path: Remote file path
        
    Requirements: 13.3
    """
    logger = logging.getLogger("bot.download")
    logger.info(f"Download completed: task_id={task_id}, title={title}, path={remote_path}")


def log_download_error(task_id: str, error: str) -> None:
    """
    Log download task error
    
    Args:
        task_id: Task ID
        error: Error message
        
    Requirements: 13.3
    """
    logger = logging.getLogger("bot.download")
    logger.error(f"Download failed: task_id={task_id}, error={error}")


def log_storage_operation(operation: str, path: str, success: bool, error: str = None) -> None:
    """
    Log WebDAV storage operation
    
    Args:
        operation: Operation type (upload, create_dir, etc.)
        path: File/directory path
        success: Whether operation succeeded
        error: Error message if failed
        
    Requirements: 13.4
    """
    logger = logging.getLogger("bot.storage")
    
    if success:
        logger.info(f"Storage operation succeeded: {operation} - {path}")
    else:
        logger.error(f"Storage operation failed: {operation} - {path} - {error}")


def log_critical_event(event: str, details: str = None) -> None:
    """
    Log critical system event
    
    Args:
        event: Event description
        details: Additional details
        
    Requirements: 13.1
    """
    logger = logging.getLogger("bot.system")
    
    if details:
        logger.critical(f"{event}: {details}")
    else:
        logger.critical(event)
