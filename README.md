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

## 📖 О проекте

**CloudTube** — это умный Telegram-бот, который автоматизирует загрузку видео с YouTube на ваше личное облачное хранилище WebDAV. Забудьте о ручном скачивании видео на компьютер и последующей загрузке в облако — CloudTube делает всё это за вас!

### 🎯 Для чего нужен CloudTube?

- **Создание личной видеотеки**: Сохраняйте любимые видео и плейлисты в своём облаке
- **Офлайн-доступ**: Смотрите видео без интернета с любого устройства, подключенного к вашему хранилищу
- **Архивирование контента**: Сохраняйте важные видео, которые могут быть удалены с YouTube
- **Экономия трафика**: Загрузите один раз, смотрите сколько угодно без повторной загрузки
- **Организация коллекций**: Автоматическая сортировка видео по плейлистам в отдельные папки

### 💡 Как это работает?

1. Вы отправляете боту ссылку на видео или плейлист YouTube
2. Выбираете качество видео (от 360p до 1080p или лучшее доступное)
3. Настраиваете уведомления о ходе загрузки
4. Бот скачивает видео и автоматически загружает его на ваше WebDAV хранилище
5. Готово! Видео доступно в вашем облаке

### 🔒 Безопасность и приватность

- Бот работает только для вас — доступ только у владельца (по Telegram ID)
- Все данные хранятся на вашем собственном WebDAV сервере
- Учетные данные WebDAV шифруются в локальной базе данных
- Никакие данные не передаются третьим лицам

### 🚀 Преимущества

- **Асинхронная работа**: Загружайте несколько видео одновременно
- **Умное управление**: Приостанавливайте, возобновляйте или отменяйте загрузки
- **Автоматическое восстановление**: Продолжает работу после перезапуска
- **Мониторинг ресурсов**: Автоматически контролирует использование памяти
- **Кросс-платформенность**: Работает на Windows, Linux и macOS

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

## 🌐 Поддерживаемые WebDAV сервисы

CloudTube работает с любым WebDAV-совместимым хранилищем:

### Популярные облачные сервисы
- ☁️ **Nextcloud** / **ownCloud** - самые популярные self-hosted решения
- 📦 **Yandex.Disk** - поддержка WebDAV из коробки
- 🌍 **Box.com** - корпоративное облако с WebDAV
- 📁 **4shared** - файловый хостинг с WebDAV API

### Self-hosted решения
- 🏠 **Synology NAS** - встроенная поддержка WebDAV
- 💾 **QNAP NAS** - WebDAV сервер в QTS
- 🖥️ **TrueNAS** - WebDAV через плагины
- 🐧 **Apache/Nginx** - настройка WebDAV модуля

### Как подключить?

```
/connect https://webdav.example.com username password
```

Примеры:
- Nextcloud: `https://cloud.example.com/remote.php/dav/files/username/`
- Yandex.Disk: `https://webdav.yandex.ru`
- Synology: `https://nas.local:5006`

### 🔐 Важно для Yandex.Disk:

Яндекс.Диск требует **пароль приложения**, а не основной пароль аккаунта!

**Как получить пароль приложения:**
1. Перейдите на https://id.yandex.ru/security/app-passwords
2. Нажмите "Создать пароль приложения"
3. Выберите тип **"Файлы"** или **"WebDAV"**
4. Скопируйте сгенерированный пароль (он показывается только один раз!)

**Подключение к Yandex.Disk:**
```
/connect https://webdav.yandex.ru ваш_email@yandex.ru пароль_приложения
```

Пример:
```
/connect https://webdav.yandex.ru ivan@yandex.ru abcd1234efgh5678
```

---

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

### 🎬 Основные сценарии

#### Загрузка одного видео

```
1. Отправьте боту ссылку:
   https://www.youtube.com/watch?v=dQw4w9WgXcQ

2. Выберите качество:
   🎬 Лучшее / 📺 1080p / 📺 720p / 📺 480p / 📺 360p

3. Настройте уведомления:
   🔔 Все / ⚠️ Важные / ❌ Только ошибки / 🔕 Без уведомлений

4. Готово! Бот начнёт загрузку
```

#### Загрузка плейлиста

```
1. Отправьте ссылку на плейлист:
   https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf

2. Выберите качество для всех видео
3. Бот создаст папку с названием плейлиста
4. Видео будут загружаться последовательно
```

#### Управление загрузками

```
/status              - Посмотреть активные загрузки
/pause task_abc123   - Приостановить загрузку
/resume task_abc123  - Возобновить загрузку
/cancel task_abc123  - Отменить загрузку
/history             - Посмотреть историю всех загрузок
```

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

---

## ❓ FAQ (Часто задаваемые вопросы)

### Общие вопросы

**Q: Можно ли использовать CloudTube для коммерческих целей?**  
A: Да, проект распространяется под лицензией MIT, которая позволяет коммерческое использование.

**Q: Сколько пользователей может использовать одного бота?**  
A: CloudTube разработан для использования одним владельцем. Для нескольких пользователей нужно запустить отдельные экземпляры бота.

**Q: Какой размер видео можно загружать?**  
A: Ограничение зависит только от свободного места на вашем WebDAV хранилище. Бот предупредит, если места недостаточно.

**Q: Можно ли загружать приватные видео?**  
A: Нет, yt-dlp (используемая библиотека) не поддерживает загрузку приватных видео, требующих авторизации.

### Технические вопросы

**Q: Какие форматы видео поддерживаются?**  
A: Все видео конвертируются в MP4 для максимальной совместимости.

**Q: Можно ли загружать только аудио?**  
A: В текущей версии нет, но эта функция планируется в будущих обновлениях.

**Q: Сколько видео можно загружать одновременно?**  
A: По умолчанию 2 видео. Можно изменить в настройках `MAX_CONCURRENT_DOWNLOADS`.

**Q: Что делать, если загрузка прервалась?**  
A: Бот автоматически помечает прерванные задачи при перезапуске. Используйте `/resume task_id` для возобновления.

### Проблемы и решения

**Q: Бот не отвечает на команды**  
A: Проверьте:
1. Правильность токена бота в `.env`
2. Ваш Telegram ID совпадает с `TELEGRAM_OWNER_ID`
3. Бот запущен: `sudo systemctl status cloudtube`

**Q: Ошибка "Failed to download video"**  
A: Возможные причины:
1. FFmpeg не установлен: `ffmpeg -version`
2. Видео недоступно или удалено
3. Проблемы с сетью или YouTube

**Q: Высокое использование памяти**  
A: Уменьшите количество параллельных загрузок в `.env`:
```bash
MAX_CONCURRENT_DOWNLOADS=1
```

**Q: WebDAV не подключается**  
A: Проверьте:
1. URL хранилища доступен: `curl -I https://your-webdav.com`
2. Правильность логина и пароля
3. WebDAV включен на сервере

**Q: Ошибка "HTTP Error 403: Forbidden" при загрузке**  
A: YouTube блокирует запросы. Решение:
1. Обновите yt-dlp до последней версии:
   ```bash
   # Linux/macOS
   ./update_ytdlp.sh
   
   # Windows
   update_ytdlp.bat
   
   # Или вручную
   pip install --upgrade yt-dlp
   ```
2. Перезапустите бота
3. Если проблема сохраняется, попробуйте другое видео или подождите несколько минут

**Q: Как обновить yt-dlp?**  
A: Используйте готовые скрипты:
- Linux/macOS: `./update_ytdlp.sh`
- Windows: `update_ytdlp.bat`
- Вручную: `pip install --upgrade yt-dlp` + перезапуск бота

---

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
