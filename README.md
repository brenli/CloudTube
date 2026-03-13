# CloudTube

<div align="center">

```
   _____ _                 _ _______    _          
  / ____| |               | |__   __|  | |         
 | |    | | ___  _   _  __| |  | |_   _| |__   ___ 
 | |    | |/ _ \| | | |/ _` |  | | | | | '_ \ / _ \
 | |____| | (_) | |_| | (_| |  | | |_| | |_) |  __/
  \_____|_|\___/ \__,_|\__,_|  |_|\__,_|_.__/ \___|
```

### 🎬 Your YouTube in the Cloud

*Telegram bot for automated YouTube video downloads to WebDAV storage*

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-86%20passed-brightgreen.svg)](tests/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](README.md)

**Created by [Kir](https://github.com/brenli)** 👨‍💻

[Features](#-features) • [Quick Start](#-quick-start) • [Installation](#-installation) • [Documentation](#-documentation)

</div>

---

## ✨ Features

- 📥 **Загрузка отдельных видео** с YouTube
- 📋 **Загрузка целых плейлистов** с автоматической организацией
- 🎬 **Выбор качества** видео (best, 1080p, 720p, 480p, 360p)
- 🔔 **Настраиваемые уведомления** для каждой загрузки
- ⏸️ **Управление загрузками** (пауза, возобновление, отмена)
- 📊 **Просмотр истории** загрузок с фильтрацией
- 💾 **Автоматическая организация** файлов в папки
- 🔄 **Восстановление** после перезапуска
- 🔒 **Безопасное хранение** учетных данных
- 📈 **Мониторинг ресурсов** с автоматическим throttling

## 🚀 Быстрый старт

### 🪟 Windows

```powershell
git clone https://github.com/brenli/CloudTube.git
cd CloudTube
.\setup.bat
# Отредактируйте .env (откроется автоматически)
.\venv\Scripts\Activate.ps1
python -m bot.main
```

📖 **Подробная инструкция для Windows**: [WINDOWS_INSTALL.md](WINDOWS_INSTALL.md)

### 🐧 Linux/Mac

```bash
git clone https://github.com/brenli/CloudTube.git
cd CloudTube
chmod +x setup.sh && ./setup.sh
nano .env  # Заполните конфигурацию
source venv/bin/activate
python -m bot.main
```

### Автоматическая установка (Linux)

```bash
curl -sSL https://raw.githubusercontent.com/brenli/CloudTube/main/install.sh | bash
```

📖 **Подробная инструкция**: [INSTALLATION.md](INSTALLATION.md)

## 📋 Требования

### Операционные системы
- ✅ **Windows 10/11** - полная поддержка ([инструкция](WINDOWS_INSTALL.md))
- ✅ **Ubuntu 22.04/24.04 LTS** - полная поддержка
- ✅ **macOS** - базовая поддержка

### Минимальные требования
- **Python**: 3.11 или выше
- **RAM**: 2GB минимум (рекомендуется 4GB)
- **CPU**: 2 ядра минимум
- **Диск**: 10GB свободного места
- **FFmpeg**: Для обработки видео
- **WebDAV**: Доступ к хранилищу

## Быстрая установка

```bash
curl -sSL https://raw.githubusercontent.com/brenli/CloudTube/main/install.sh | bash
```

## Ручная установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/brenli/CloudTube.git
cd CloudTube
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

### 5. Запуск

```bash
python -m bot.main
```

## Установка как системный сервис

```bash
sudo cp systemd/cloudtube.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cloudtube
sudo systemctl start cloudtube
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
DATABASE_PATH=/var/lib/CloudTube/bot.db

# Downloads
TEMP_DOWNLOAD_PATH=/tmp/CloudTube
MAX_CONCURRENT_DOWNLOADS=2

# Logging
LOG_LEVEL=INFO
LOG_PATH=/var/log/CloudTube
```

Подробное описание всех параметров см. в [.env.example](.env.example)

## Мониторинг

### Просмотр логов

```bash
# Системные логи
sudo journalctl -u cloudtube -f

# Логи приложения
tail -f logs/bot.log
```

### Статус сервиса

```bash
sudo systemctl status cloudtube
```

### Перезапуск

```bash
sudo systemctl restart cloudtube
```

## Обновление

```bash
cd /opt/CloudTube
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart cloudtube
```

## Резервное копирование

### База данных

```bash
# Ручное резервное копирование
sqlite3 /var/lib/CloudTube/bot.db ".backup '/backup/bot.db'"

# Автоматическое резервное копирование (cron)
0 2 * * * sqlite3 /var/lib/CloudTube/bot.db ".backup '/backup/bot-$(date +\%Y\%m\%d).db'"
```

## Устранение неполадок

### Бот не отвечает

1. Проверьте статус сервиса: `sudo systemctl status cloudtube`
2. Проверьте логи: `sudo journalctl -u cloudtube -n 50`
3. Проверьте токен бота в `.env`

### Ошибки загрузки

1. Проверьте подключение к WebDAV: `/status`
2. Проверьте доступное место в хранилище
3. Проверьте логи загрузки: `tail -f logs/bot.log`

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
CloudTube/
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

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

Copyright (c) 2026 Kir

## 👨‍💻 Author

**CloudTube** is created and maintained by **Kir**

- 🌟 If you like this project, give it a star!
- 🐛 Found a bug? [Open an issue](https://github.com/brenli/CloudTube/issues)
- 💡 Have an idea? [Contribute](CONTRIBUTING.md)!

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 💬 Support

If you have questions or problems:

1. Check the [documentation](README.md)
2. See [installation guide](INSTALLATION.md)
3. Open an [issue](https://github.com/brenli/CloudTube/issues)

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- [webdav4](https://github.com/skshetry/webdav4) - WebDAV client

---

<div align="center">

**CloudTube** - Your YouTube in the Cloud

Made with ❤️ by [Kir](https://github.com/brenli)

⭐ Star this project if you find it useful!

</div>
