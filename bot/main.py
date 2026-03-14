"""
Main entry point for YouTube WebDAV Bot

Initializes all services and starts the bot.
"""

import asyncio
import signal
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.config import ConfigManager
from bot.database import Database
from bot.auth import AuthService
from bot.webdav import WebDAVService
from bot.notification import NotificationService
from bot.download import DownloadManager, TaskExecutor
from bot.progress import ProgressTracker
from bot.bot_handler import BotHandler
from bot.resource_monitor import ResourceMonitor
from bot.logging_config import setup_logging, log_critical_event


async def main():
    """Main application entry point"""
    
    # Load configuration
    try:
        config = ConfigManager.load_from_env()
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Setup logging
    setup_logging(log_dir=config.log_path, log_level=config.log_level)
    log_critical_event("Bot starting")
    
    # Initialize database
    db = Database(config.database_path)
    await db.initialize()
    
    # Initialize services
    auth_service = AuthService(config.owner_id)
    webdav_service = WebDAVService()
    notification_service = NotificationService()
    progress_tracker = ProgressTracker()
    
    # Initialize task executor
    task_executor = TaskExecutor(
        webdav_service=webdav_service,
        temp_dir=config.temp_download_path
    )
    
    # Initialize download manager
    download_manager = DownloadManager(
        database=db,
        task_executor=task_executor,
        progress_tracker=progress_tracker,
        notification_service=notification_service,
        max_concurrent=config.max_concurrent_downloads
    )
    
    # Initialize resource monitor
    resource_monitor = ResourceMonitor()
    resource_monitor.set_download_manager(download_manager)
    
    # Initialize bot handler
    bot_handler = BotHandler(
        token=config.telegram_token,
        auth_service=auth_service,
        download_manager=download_manager,
        webdav_service=webdav_service,
        notification_service=notification_service
    )
    
    # Set bot for notification service
    notification_service.set_bot(bot_handler.application)
    notification_service.set_owner_id(config.owner_id)
    
    # Restore interrupted tasks
    log_critical_event("Restoring interrupted tasks")
    restore_result = await download_manager.restore_interrupted_tasks()
    
    if restore_result["interrupted_count"] > 0:
        log_critical_event(
            f"Found {restore_result['interrupted_count']} interrupted tasks"
        )
    
    # Start services
    await download_manager.start()
    await resource_monitor.start_monitoring()
    
    # Start bot
    log_critical_event("Starting bot")
    await bot_handler.start()
    
    # Setup signal handlers
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        log_critical_event("Shutdown signal received")
        asyncio.create_task(shutdown(
            bot_handler,
            download_manager,
            resource_monitor,
            db
        ))
    
    # Windows and Unix have different signal handling
    import platform
    if platform.system() != 'Windows':
        # Unix-like systems
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, signal_handler)
    else:
        # Windows - use signal.signal instead
        def windows_signal_handler(signum, frame):
            signal_handler()
        
        signal.signal(signal.SIGINT, windows_signal_handler)
        signal.signal(signal.SIGTERM, windows_signal_handler)
    
    log_critical_event("Bot started successfully")
    
    # Keep running
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        pass


async def shutdown(bot_handler, download_manager, resource_monitor, db):
    """Graceful shutdown"""
    log_critical_event("Shutting down")
    
    # Stop bot
    await bot_handler.stop()
    
    # Stop download manager
    await download_manager.stop()
    
    # Stop resource monitor
    await resource_monitor.stop_monitoring()
    
    # Close database
    await db.close()
    
    log_critical_event("Shutdown complete")
    
    # Exit
    sys.exit(0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
