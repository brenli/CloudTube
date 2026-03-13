# YouTube WebDAV Bot

Telegram-бот для автоматизированной загрузки видео с YouTube на внешнее WebDAV хранилище.

## Возможности

- 📥 Загрузка отдельных видео с YouTube
- 📋 Загрузка целых плейлистов
- 🎬 Выбор качества видео (best, 1080p, 720p, 480p, 360p)
- 🔔 Настраиваемые уведомления
- ⏸️ Приостановка и возобновление загрузок
- 📊 Просмотр истории загрузок
- 💾 Автоматическая организация файлов
- 🔄 Восстановление после перезапуска
- 🔒 Безопасное хранение учетных данных

## Требования

- Ubuntu 22.04 или 24.04 LTS
- Python 3.11+
- 2GB RAM минимум
- 2 CPU cores минимум
- 10GB свободного места для временных файлов
- WebDAV хранилище

## Быстрая установка

```bash
curl -sSL https://raw.githubusercontent.com/user/youtube-webdav-bot/main/install.sh | bash
```

## Ручная установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/user/youtube-webdav-bot.git
cd youtube-webdav-bot
```

### 2. Установка зависимостей

```bash
# Установка Python 3.11
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Установка системных зависимостей
sudo apt install -y python3-pip ffmpeg sqlite3 git
```

### 3. Создание виртуального окружения

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Конфигурация

```bash
cp .env.example .env
nano .env
```

Заполните обязательные параметры:
- `TELEGRAM_BOT_TOKEN` - токен вашего Telegram бота
- `TELEGRAM_OWNER_ID` - ваш Telegram ID

### 5. Инициализация базы данных

```bash
python -m bot.database init
```

### 6. Запуск

```bash
python -m bot.main
```

## Установка как системный сервис

```bash
sudo cp systemd/youtube-webdav-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable youtube-webdav-bot
sudo systemctl start youtube-webdav-bot
```

## Использование

### Команды бота

- `/start` - Приветственное сообщение и список команд
- `/help` - Подробная справка по командам
- `/connect <url> <username> <password>` - Подключение к WebDAV
- `/status` - Статус системы и активные загрузки
- `/history [status]` - История загрузок
- `/cancel <task_id>` - Отмена загрузки
- `/pause <task_id>` - Приостановка загрузки
- `/resume <task_id>` - Возобновление загрузки

### Загрузка видео

1. Отправьте боту ссылку на видео или плейлист YouTube
2. Выберите качество видео
3. Настройте уведомления
4. Дождитесь завершения загрузки

### Пример

```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

Бот предложит выбрать качество и настройки уведомлений, затем начнет загрузку.

## Конфигурация

Все параметры настраиваются через файл `.env`:

```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_OWNER_ID=your_telegram_id_here

# Database
DATABASE_PATH=/var/lib/youtube-webdav-bot/bot.db

# Downloads
TEMP_DOWNLOAD_PATH=/tmp/youtube-webdav-bot
MAX_CONCURRENT_DOWNLOADS=2

# Logging
LOG_LEVEL=INFO
LOG_PATH=/var/log/youtube-webdav-bot
```

Подробное описание всех параметров см. в [CONFIGURATION.md](CONFIGURATION.md)

## Мониторинг

### Просмотр логов

```bash
# Системные логи
sudo journalctl -u youtube-webdav-bot -f

# Логи приложения
tail -f /var/log/youtube-webdav-bot/bot.log
```

### Статус сервиса

```bash
sudo systemctl status youtube-webdav-bot
```

### Перезапуск

```bash
sudo systemctl restart youtube-webdav-bot
```

## Обновление

```bash
cd /opt/youtube-webdav-bot
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart youtube-webdav-bot
```

## Резервное копирование

### База данных

```bash
# Ручное резервное копирование
sqlite3 /var/lib/youtube-webdav-bot/bot.db ".backup '/backup/bot.db'"

# Автоматическое резервное копирование (cron)
0 2 * * * sqlite3 /var/lib/youtube-webdav-bot/bot.db ".backup '/backup/bot-$(date +\%Y\%m\%d).db'"
```

## Устранение неполадок

### Бот не отвечает

1. Проверьте статус сервиса: `sudo systemctl status youtube-webdav-bot`
2. Проверьте логи: `sudo journalctl -u youtube-webdav-bot -n 50`
3. Проверьте токен бота в `.env`

### Ошибки загрузки

1. Проверьте подключение к WebDAV: `/status`
2. Проверьте доступное место в хранилище
3. Проверьте логи загрузки: `tail -f /var/log/youtube-webdav-bot/bot.log`

### Высокое использование памяти

Бот автоматически ограничивает загрузки при высоком использовании памяти (>80%). Если проблема сохраняется:

1. Уменьшите `MAX_CONCURRENT_DOWNLOADS` в `.env`
2. Перезапустите бот

## Разработка

### Запуск тестов

```bash
# Все тесты
pytest

# Unit тесты
pytest tests/ -k "not properties"

# Property-based тесты
pytest tests/ -k "properties"

# С покрытием
pytest --cov=bot --cov-report=html
```

### Структура проекта

```
youtube-webdav-bot/
├── bot/                    # Основной код
│   ├── auth.py            # Аутентификация
│   ├── bot_handler.py     # Telegram бот
│   ├── config.py          # Конфигурация
│   ├── database.py        # База данных
│   ├── download.py        # Загрузка видео
│   ├── logging_config.py  # Логирование
│   ├── main.py            # Точка входа
│   ├── notification.py    # Уведомления
│   ├── progress.py        # Отслеживание прогресса
│   ├── resource_monitor.py # Мониторинг ресурсов
│   └── webdav.py          # WebDAV клиент
├── tests/                 # Тесты
├── systemd/               # Systemd сервис
├── .env.example           # Пример конфигурации
├── install.sh             # Скрипт установки
├── requirements.txt       # Python зависимости
└── README.md              # Документация
```

## Лицензия

MIT License

## Поддержка

Если у вас возникли вопросы или проблемы:

1. Проверьте [документацию](README.md)
2. Посмотрите [примеры использования](USAGE.md)
3. Создайте [issue](https://github.com/user/youtube-webdav-bot/issues)

## Благодарности

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- [webdav4](https://github.com/skshetry/webdav4) - WebDAV client
