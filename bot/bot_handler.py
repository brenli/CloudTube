"""
Bot Handler and Command Router

Handles Telegram bot interactions, command routing, and message processing.
Integrates with all services to provide complete bot functionality.

Requirements: 1.2, 1.3, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 12.9
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from typing import Optional
import logging


logger = logging.getLogger(__name__)


class CommandRouter:
    """Routes commands to appropriate handlers"""
    
    def __init__(
        self,
        auth_service,
        download_manager,
        webdav_service,
        notification_service,
        database
    ):
        """
        Initialize command router
        
        Args:
            auth_service: AuthService instance
            download_manager: DownloadManager instance
            webdav_service: WebDAVService instance
            notification_service: NotificationService instance
            database: Database instance
        """
        self.auth = auth_service
        self.download_manager = download_manager
        self.webdav = webdav_service
        self.notification = notification_service
        self.database = database
    
    async def handle_start(self, user_id: int) -> str:
        """
        Handle /start command
        
        Requirements: 12.1
        """
        return """
🎬 Добро пожаловать в YouTube WebDAV Bot!

Я помогу вам загружать видео с YouTube на ваше WebDAV хранилище.

📋 Доступные команды:
/help - Показать справку по командам
/connect - Подключиться к WebDAV хранилищу
/status - Показать статус системы
/history - Показать историю загрузок
/cancel <task_id> - Отменить загрузку
/pause <task_id> - Приостановить загрузку
/resume <task_id> - Возобновить загрузку

Просто отправьте мне ссылку на видео или плейлист YouTube, и я начну загрузку!
"""
    
    async def handle_help(self, user_id: int) -> str:
        """
        Handle /help command
        
        Requirements: 12.2
        """
        return """
📖 Справка по командам:

🔗 /connect - Подключение к WebDAV
Формат: /connect <url> <username> <password>
Пример: /connect https://webdav.example.com user pass123

📊 /status - Статус системы
Показывает:
- Статус подключения к хранилищу
- Доступное место
- Активные загрузки

📜 /history [status] - История загрузок
Показывает все загрузки или фильтрует по статусу
Статусы: completed, failed, cancelled, paused

❌ /cancel <task_id> - Отмена загрузки
Останавливает загрузку и удаляет временные файлы

⏸ /pause <task_id> - Приостановка загрузки
Приостанавливает загрузку с сохранением прогресса

▶️ /resume <task_id> - Возобновление загрузки
Продолжает приостановленную загрузку

🎥 Загрузка видео:
Просто отправьте ссылку на видео или плейлист YouTube
"""
    
    async def handle_status(self, user_id: int) -> str:
        """
        Handle /status command
        
        Requirements: 12.3
        """
        # Check WebDAV connection
        webdav_connected = await self.webdav.test_connection()
        
        status_text = "📊 Статус системы\n\n"
        
        # WebDAV status
        if webdav_connected:
            storage_info = await self.webdav.get_storage_info()
            free_gb = storage_info.free_space / (1024**3)
            total_gb = storage_info.total_space / (1024**3)
            used_percent = (storage_info.used_space / storage_info.total_space) * 100
            
            status_text += f"✅ WebDAV: Подключено\n"
            status_text += f"💾 Место: {free_gb:.2f} GB свободно из {total_gb:.2f} GB ({used_percent:.1f}% использовано)\n\n"
        else:
            status_text += "❌ WebDAV: Не подключено\n"
            status_text += "Используйте /connect для подключения\n\n"
        
        # Active tasks
        active_tasks = await self.download_manager.get_active_tasks()
        
        if active_tasks:
            status_text += f"📥 Активные загрузки: {len(active_tasks)}\n\n"
            for task in active_tasks[:5]:  # Show first 5
                progress_percent = task.progress * 100
                status_text += f"• {task.title[:40]}...\n"
                status_text += f"  Статус: {task.status.value}, Прогресс: {progress_percent:.1f}%\n"
                status_text += f"  ID: {task.task_id}\n\n"
            
            if len(active_tasks) > 5:
                status_text += f"... и еще {len(active_tasks) - 5} загрузок\n"
        else:
            status_text += "📥 Нет активных загрузок\n"
        
        return status_text
    
    async def handle_history(self, user_id: int, status_filter: Optional[str] = None) -> str:
        """
        Handle /history command
        
        Requirements: 12.4
        """
        tasks = await self.download_manager.get_history(status_filter)
        
        if not tasks:
            if status_filter:
                return f"📜 История загрузок (фильтр: {status_filter})\n\nЗагрузок не найдено"
            return "📜 История загрузок\n\nИстория пуста"
        
        history_text = f"📜 История загрузок"
        if status_filter:
            history_text += f" (фильтр: {status_filter})"
        history_text += f"\n\nВсего: {len(tasks)}\n\n"
        
        # Show last 10 tasks
        for task in tasks[:10]:
            status_emoji = {
                "completed": "✅",
                "failed": "❌",
                "cancelled": "🚫",
                "paused": "⏸",
                "downloading": "⬇️",
                "pending": "⏳"
            }.get(task.status.value, "❓")
            
            history_text += f"{status_emoji} {task.title[:40]}...\n"
            history_text += f"  Качество: {task.quality}, Статус: {task.status.value}\n"
            history_text += f"  Дата: {task.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            history_text += f"  ID: {task.task_id}\n\n"
        
        if len(tasks) > 10:
            history_text += f"... и еще {len(tasks) - 10} загрузок\n"
        
        return history_text
    
    async def handle_cancel(self, user_id: int, task_id: str) -> str:
        """
        Handle /cancel command
        
        Requirements: 12.5
        """
        if not task_id:
            return "❌ Укажите ID задачи: /cancel <task_id>"
        
        success = await self.download_manager.cancel_task(task_id)
        
        if success:
            return f"✅ Загрузка {task_id} отменена"
        else:
            return f"❌ Не удалось отменить загрузку {task_id}\nВозможно, задача уже завершена или не существует"
    
    async def handle_pause(self, user_id: int, task_id: str) -> str:
        """
        Handle /pause command
        
        Requirements: 12.6
        """
        if not task_id:
            return "❌ Укажите ID задачи: /pause <task_id>"
        
        success = await self.download_manager.pause_task(task_id)
        
        if success:
            return f"⏸ Загрузка {task_id} приостановлена"
        else:
            return f"❌ Не удалось приостановить загрузку {task_id}\nВозможно, задача не выполняется"
    
    async def handle_resume(self, user_id: int, task_id: str) -> str:
        """
        Handle /resume command
        
        Requirements: 12.7
        """
        if not task_id:
            return "❌ Укажите ID задачи: /resume <task_id>"
        
        success = await self.download_manager.resume_task(task_id)
        
        if success:
            return f"▶️ Загрузка {task_id} возобновлена"
        else:
            return f"❌ Не удалось возобновить загрузку {task_id}\nВозможно, задача не приостановлена"
    
    async def handle_connect(self, user_id: int, url: str, username: str, password: str) -> str:
        """
        Handle /connect command
        
        Requirements: 12.8
        """
        if not url or not username or not password:
            return """
❌ Неверный формат команды

Использование: /connect <url> <username> <password_or_token>

Для БЫСТРОЙ загрузки используйте OAuth токен (начинается с y0_, y1_, y2_, y3_)
Для медленной загрузки можно использовать app password

Пример: /connect https://webdav.yandex.ru user@yandex.ru y0_xxxxx
"""
        
        from bot.database import WebDAVConfig
        
        config = WebDAVConfig(url=url, username=username, password=password)
        
        # Check if OAuth token
        is_oauth = password.startswith(("y0_", "y1_", "y2_", "y3_", "t1.", "AQAA"))
        
        try:
            # Test connection
            success = await self.webdav.connect(config)
            
            if success:
                # Save config to database
                await self.database.save_webdav_config(config)
                
                if is_oauth:
                    return f"✅ Успешно подключено к {url}\n💾 Конфигурация сохранена\n🚀 OAuth токен обнаружен - загрузка будет БЫСТРОЙ через REST API"
                else:
                    return f"✅ Успешно подключено к {url}\n💾 Конфигурация сохранена\n⚠️ App password обнаружен - загрузка будет МЕДЛЕННОЙ через WebDAV\n\nДля быстрой загрузки получите OAuth токен: python get_yandex_token.py"
            else:
                return f"❌ Не удалось подключиться к {url}\nПроверьте учетные данные"
        except Exception as e:
            return f"❌ Ошибка подключения: {str(e)}"


class BotHandler:
    """Main bot handler for Telegram interactions"""
    
    def __init__(
        self,
        token: str,
        auth_service,
        download_manager,
        webdav_service,
        notification_service,
        database
    ):
        """
        Initialize bot handler
        
        Args:
            token: Telegram bot token
            auth_service: AuthService instance
            download_manager: DownloadManager instance
            webdav_service: WebDAVService instance
            notification_service: NotificationService instance
            database: Database instance
        """
        self.token = token
        self.auth = auth_service
        self.router = CommandRouter(
            auth_service,
            download_manager,
            webdav_service,
            notification_service,
            database
        )
        self.download_manager = download_manager
        self.application: Optional[Application] = None
    
    async def start(self) -> None:
        """Start the bot"""
        # Build application
        self.application = Application.builder().token(self.token).build()
        
        # Add command handlers
        self.application.add_handler(CommandHandler("start", self._handle_start))
        self.application.add_handler(CommandHandler("help", self._handle_help))
        self.application.add_handler(CommandHandler("status", self._handle_status))
        self.application.add_handler(CommandHandler("history", self._handle_history))
        self.application.add_handler(CommandHandler("cancel", self._handle_cancel))
        self.application.add_handler(CommandHandler("pause", self._handle_pause))
        self.application.add_handler(CommandHandler("resume", self._handle_resume))
        self.application.add_handler(CommandHandler("connect", self._handle_connect))
        
        # Add message handler for URLs
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message)
        )
        
        # Add callback query handler for inline buttons
        self.application.add_handler(CallbackQueryHandler(self._handle_callback))
        
        # Start bot
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        logger.info("Bot started successfully")
    
    async def stop(self) -> None:
        """Stop the bot"""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            logger.info("Bot stopped")
    
    def _check_auth(self, update: Update) -> bool:
        """Check if user is authorized"""
        user_id = update.effective_user.id
        if not self.auth.is_owner(user_id):
            return False
        return True
    
    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        if not self._check_auth(update):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        response = await self.router.handle_start(update.effective_user.id)
        await update.message.reply_text(response)
    
    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command"""
        if not self._check_auth(update):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        response = await self.router.handle_help(update.effective_user.id)
        await update.message.reply_text(response)
    
    async def _handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command"""
        if not self._check_auth(update):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        response = await self.router.handle_status(update.effective_user.id)
        await update.message.reply_text(response)
    
    async def _handle_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /history command"""
        if not self._check_auth(update):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        status_filter = context.args[0] if context.args else None
        response = await self.router.handle_history(update.effective_user.id, status_filter)
        await update.message.reply_text(response)
    
    async def _handle_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /cancel command"""
        if not self._check_auth(update):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        task_id = context.args[0] if context.args else None
        response = await self.router.handle_cancel(update.effective_user.id, task_id)
        await update.message.reply_text(response)
    
    async def _handle_pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /pause command"""
        if not self._check_auth(update):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        task_id = context.args[0] if context.args else None
        response = await self.router.handle_pause(update.effective_user.id, task_id)
        await update.message.reply_text(response)
    
    async def _handle_resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /resume command"""
        if not self._check_auth(update):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        task_id = context.args[0] if context.args else None
        response = await self.router.handle_resume(update.effective_user.id, task_id)
        await update.message.reply_text(response)
    
    async def _handle_connect(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /connect command"""
        if not self._check_auth(update):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        if len(context.args) < 3:
            response = await self.router.handle_connect(update.effective_user.id, "", "", "")
        else:
            url, username, password = context.args[0], context.args[1], context.args[2]
            response = await self.router.handle_connect(update.effective_user.id, url, username, password)
        
        await update.message.reply_text(response)
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle text messages (YouTube URLs)
        
        Requirements: 3.1, 3.2, 3.3, 6.1
        """
        if not self._check_auth(update):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        text = update.message.text
        
        # Check if it's a YouTube URL
        if not ("youtube.com" in text or "youtu.be" in text):
            await update.message.reply_text(
                "❓ Неизвестная команда. Используйте /help для справки"
            )
            return
        
        # Store URL in context for callback
        context.user_data['url'] = text
        
        # Show quality selection
        keyboard = [
            [
                InlineKeyboardButton("🎬 Лучшее", callback_data="quality_best"),
                InlineKeyboardButton("📺 1080p", callback_data="quality_1080p")
            ],
            [
                InlineKeyboardButton("📺 720p", callback_data="quality_720p"),
                InlineKeyboardButton("📺 480p", callback_data="quality_480p")
            ],
            [InlineKeyboardButton("📺 360p", callback_data="quality_360p")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🎬 Выберите качество видео:",
            reply_markup=reply_markup
        )
    
    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        
        if not self._check_auth(update):
            await query.edit_message_text("❌ Доступ запрещен")
            return
        
        data = query.data
        
        # Handle quality selection
        if data.startswith("quality_"):
            quality = data.replace("quality_", "")
            url = context.user_data.get('url')
            
            if not url:
                await query.edit_message_text("❌ Ошибка: URL не найден")
                return
            
            # Show notification settings
            context.user_data['quality'] = quality
            
            keyboard = [
                [InlineKeyboardButton("🔔 Все уведомления", callback_data="notif_all")],
                [InlineKeyboardButton("⚠️ Только важные", callback_data="notif_important")],
                [InlineKeyboardButton("❌ Только ошибки", callback_data="notif_errors")],
                [InlineKeyboardButton("🔕 Без уведомлений", callback_data="notif_none")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"✅ Качество: {quality}\n\n🔔 Выберите настройки уведомлений:",
                reply_markup=reply_markup
            )
        
        # Handle notification settings
        elif data.startswith("notif_"):
            from bot.database import NotificationSettings
            
            notif_type = data.replace("notif_", "")
            url = context.user_data.get('url')
            quality = context.user_data.get('quality')
            
            if not url or not quality:
                await query.edit_message_text("❌ Ошибка: данные не найдены")
                return
            
            # Create notification settings
            if notif_type == "all":
                settings = NotificationSettings.all_notifications()
            elif notif_type == "important":
                settings = NotificationSettings.important_only()
            elif notif_type == "errors":
                settings = NotificationSettings.errors_only()
            else:
                settings = NotificationSettings.no_notifications()
            
            # Create download task
            try:
                # Check if it's a playlist
                if "playlist" in url or "list=" in url:
                    await query.edit_message_text("📥 Обработка плейлиста...")
                    playlist_id, tasks = await self.download_manager.create_playlist_tasks(
                        url, quality, settings
                    )
                    await query.edit_message_text(
                        f"✅ Создано {len(tasks)} задач для плейлиста\n"
                        f"ID плейлиста: {playlist_id}\n\n"
                        f"Загрузка начнется автоматически"
                    )
                else:
                    await query.edit_message_text("📥 Создание задачи загрузки...")
                    task = await self.download_manager.create_download_task(
                        url, quality, settings
                    )
                    await query.edit_message_text(
                        f"✅ Задача создана\n"
                        f"Название: {task.title}\n"
                        f"Качество: {quality}\n"
                        f"ID: {task.task_id}\n\n"
                        f"Загрузка начнется автоматически"
                    )
            except ValueError as e:
                await query.edit_message_text(f"❌ Ошибка: {str(e)}")
            except Exception as e:
                await query.edit_message_text(f"❌ Неожиданная ошибка: {str(e)}")
                logger.error(f"Error creating download task: {e}", exc_info=True)
