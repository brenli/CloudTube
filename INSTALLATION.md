# 📦 Installation Guide - CloudTube

**CloudTube** - Your YouTube in the Cloud

*Created by Kir*

---

## Содержание

1. [Требования](#требования)
2. [Быстрая установка (Windows)](#быстрая-установка-windows)
3. [Быстрая установка (Linux)](#быстрая-установка-linux)
4. [Ручная установка](#ручная-установка)
5. [Настройка Telegram бота](#настройка-telegram-бота)
6. [Первый запуск](#первый-запуск)
7. [Установка как сервис (Linux)](#установка-как-сервис-linux)
8. [Устранение проблем](#устранение-проблем)

---

## Требования

### Минимальные требования

- **ОС**: Windows 10/11 или Ubuntu 22.04/24.04 LTS
- **Python**: 3.11 или выше
- **RAM**: 2GB минимум (рекомендуется 4GB)
- **CPU**: 2 ядра минимум
- **Диск**: 10GB свободного места для временных файлов
- **Интернет**: Стабильное подключение
- **WebDAV**: Доступ к WebDAV хранилищу

### Дополнительные требования

- **FFmpeg**: Для обработки видео (устанавливается автоматически)
- **Git**: Для клонирования репозитория

---

## Быстрая установка (Windows)

### Шаг 1: Установка Python

1. Скачайте Python 3.11+ с [python.org](https://www.python.org/downloads/)
2. Запустите установщик
3. ✅ **ВАЖНО**: Отметьте "Add Python to PATH"
4. Нажмите "Install Now"

### Шаг 2: Установка FFmpeg

1. Скачайте FFmpeg с [ffmpeg.org](https://ffmpeg.org/download.html)
2. Распакуйте архив в `C:\ffmpeg`
3. Добавьте `C:\ffmpeg\bin` в PATH:
   - Откройте "Система" → "Дополнительные параметры системы"
   - "Переменные среды" → "Path" → "Изменить"
   - Добавьте `C:\ffmpeg\bin`

### Шаг 3: Клонирование проекта

```powershell
# Откройте PowerShell
cd C:\Projects
git clone https://github.com/brenli/CloudTube.git
cd CloudTube
```

### Шаг 4: Запуск установки

```powershell
# Запустите setup.bat
.\setup.bat
```

Скрипт автоматически:
- Создаст виртуальное окружение
- Установит все зависимости
- Создаст необходимые директории
- Скопирует .env.example в .env

### Шаг 5: Настройка

```powershell
# Откройте .env в блокноте
notepad .env
```

Заполните обязательные параметры (см. [Настройка Telegram бота](#настройка-telegram-бота))

### Шаг 6: Запуск

```powershell
# Активируйте виртуальное окружение
.\venv\Scripts\Activate.ps1

# Запустите бота
python -m bot.main
```

---

## Быстрая установка (Linux)

### Способ 1: Автоматическая установка (рекомендуется)

```bash
# Скачайте и запустите скрипт установки
curl -sSL https://raw.githubusercontent.com/brenli/CloudTube/main/install.sh | bash
```

Скрипт автоматически клонирует репозиторий и установит всё необходимое.

### Способ 2: Установка из клонированного репозитория

Если вы уже клонировали репозиторий:

```bash
git clone https://github.com/brenli/CloudTube.git
cd CloudTube
chmod +x setup.sh
./setup.sh
```

Затем настройте как сервис вручную (см. [Установка как сервис](#установка-как-сервис-linux)).

### Что делает автоматическая установка:
- Проверит ОС (Ubuntu 22/24)
- Установит Python 3.11
- Установит системные зависимости (FFmpeg, SQLite, Git)
- Клонирует репозиторий в `/opt/CloudTube`
- Создаст виртуальное окружение
- Установит Python зависимости
- Создаст директории данных
- Настроит systemd сервис

### После установки

```bash
# Отредактируйте конфигурацию
nano /opt/CloudTube/.env

# Запустите бота
sudo systemctl start cloudtube

# Проверьте статус
sudo systemctl status cloudtube

# Просмотр логов
sudo journalctl -u cloudtube -f
```

---

## Ручная установка

### Шаг 1: Установка зависимостей

#### Ubuntu/Debian

```bash
# Обновление системы
sudo apt update
sudo apt upgrade -y

# Установка Python 3.11
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Установка системных зависимостей
sudo apt install -y \
    python3-pip \
    ffmpeg \
    sqlite3 \
    git \
    curl
```

#### Windows

См. [Быстрая установка (Windows)](#быстрая-установка-windows)

### Шаг 2: Клонирование репозитория

```bash
# Клонирование
git clone https://github.com/brenli/CloudTube.git
cd CloudTube
```

### Шаг 3: Создание виртуального окружения

```bash
# Создание venv
python3.11 -m venv venv

# Активация (Linux/Mac)
source venv/bin/activate

# Активация (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Активация (Windows CMD)
.\venv\Scripts\activate.bat
```

### Шаг 4: Установка Python зависимостей

```bash
# Обновление pip
pip install --upgrade pip

# Установка зависимостей
pip install -r requirements.txt
```

### Шаг 5: Создание директорий

```bash
# Linux
mkdir -p data logs temp

# Windows
mkdir data
mkdir logs
mkdir temp
```

### Шаг 6: Конфигурация

```bash
# Копирование примера конфигурации
cp .env.example .env

# Редактирование (Linux)
nano .env

# Редактирование (Windows)
notepad .env
```

---

## Настройка Telegram бота

### Шаг 1: Создание бота

1. Откройте Telegram
2. Найдите [@BotFather](https://t.me/BotFather)
3. Отправьте команду `/newbot`
4. Следуйте инструкциям:
   - Введите имя бота (например: "My YouTube Downloader")
   - Введите username бота (должен заканчиваться на "bot", например: "my_youtube_dl_bot")
5. Скопируйте токен, который вы получите (выглядит как `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Шаг 2: Получение вашего Telegram ID

1. Найдите [@userinfobot](https://t.me/userinfobot)
2. Отправьте команду `/start`
3. Скопируйте ваш ID (число, например: `123456789`)

### Шаг 3: Заполнение .env

Откройте файл `.env` и заполните:

```bash
# Вставьте токен от BotFather
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Вставьте ваш Telegram ID
TELEGRAM_OWNER_ID=123456789

# Остальные параметры можно оставить по умолчанию
DATABASE_PATH=./data/bot.db
TEMP_DOWNLOAD_PATH=./temp
MAX_CONCURRENT_DOWNLOADS=2
LOG_LEVEL=INFO
LOG_PATH=./logs
```

---

## Первый запуск

### Проверка конфигурации

```bash
# Активируйте виртуальное окружение (если не активировано)
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\Activate.ps1  # Windows

# Проверьте конфигурацию
python -c "from bot.config import AppConfig; config = AppConfig.load_from_env(); print('✅ Конфигурация корректна')"
```

### Инициализация базы данных

```bash
# База данных инициализируется автоматически при первом запуске
# Но вы можете проверить это вручную:
python -c "
import asyncio
from bot.database import Database
from bot.config import AppConfig

async def init():
    config = AppConfig.load_from_env()
    db = Database(config.database_path)
    await db.initialize()
    await db.close()
    print('✅ База данных инициализирована')

asyncio.run(init())
"
```

### Запуск бота

```bash
# Запуск
python -m bot.main
```

Вы должны увидеть:

```
2026-03-14 12:00:00 - root - INFO - Logging initialized
2026-03-14 12:00:00 - root - CRITICAL - Bot starting
2026-03-14 12:00:00 - root - CRITICAL - Restoring interrupted tasks
2026-03-14 12:00:00 - root - CRITICAL - Starting bot
2026-03-14 12:00:00 - root - INFO - Resource monitoring started
2026-03-14 12:00:00 - root - INFO - Bot started successfully
2026-03-14 12:00:00 - root - CRITICAL - Bot started successfully
```

### Проверка работы

1. Откройте Telegram
2. Найдите вашего бота по username
3. Отправьте команду `/start`
4. Вы должны получить приветственное сообщение

---

## Установка как сервис (Linux)

### Автоматическая установка

Если вы использовали `install.sh`, сервис уже установлен. Пропустите к [Управление сервисом](#управление-сервисом).

### Ручная установка сервиса

```bash
# Копирование файла сервиса
sudo cp systemd/cloudtube.service /etc/systemd/system/

# Редактирование пути (если установлено не в /opt)
sudo nano /etc/systemd/system/cloudtube.service

# Замените:
# WorkingDirectory=/opt/CloudTube
# Environment="PATH=/opt/CloudTube/venv/bin"
# ExecStart=/opt/CloudTube/venv/bin/python -m bot.main
# 
# На ваш путь, например:
# WorkingDirectory=/home/user/CloudTube
# Environment="PATH=/home/user/CloudTube/venv/bin"
# ExecStart=/home/user/CloudTube/venv/bin/python -m bot.main

# Также замените User на вашего пользователя:
# User=your_username

# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable cloudtube
```

### Управление сервисом

```bash
# Запуск
sudo systemctl start cloudtube

# Остановка
sudo systemctl stop cloudtube

# Перезапуск
sudo systemctl restart cloudtube

# Статус
sudo systemctl status cloudtube

# Просмотр логов
sudo journalctl -u cloudtube -f

# Просмотр последних 100 строк логов
sudo journalctl -u cloudtube -n 100

# Отключение автозапуска
sudo systemctl disable cloudtube
```

---

## Устранение проблем

### Бот не запускается

#### Проблема: "ModuleNotFoundError"

```bash
# Убедитесь, что виртуальное окружение активировано
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\Activate.ps1  # Windows

# Переустановите зависимости
pip install -r requirements.txt
```

#### Проблема: "Configuration error"

```bash
# Проверьте .env файл
cat .env  # Linux/Mac
type .env  # Windows

# Убедитесь, что все обязательные параметры заполнены:
# - TELEGRAM_BOT_TOKEN
# - TELEGRAM_OWNER_ID
```

#### Проблема: "Permission denied" (Linux)

```bash
# Дайте права на выполнение
chmod +x install.sh
chmod +x setup.sh

# Проверьте права на директории
ls -la data logs temp

# Если нужно, измените владельца
sudo chown -R $USER:$USER data logs temp
```

### Бот не отвечает в Telegram

#### Проверка 1: Токен бота

```bash
# Проверьте токен через Telegram API
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe

# Должен вернуть информацию о боте
```

#### Проверка 2: Логи

```bash
# Проверьте логи на ошибки
tail -f logs/bot.log  # Linux/Mac
Get-Content logs\bot.log -Tail 50  # Windows PowerShell
```

#### Проверка 3: Сеть

```bash
# Проверьте доступ к Telegram API
ping api.telegram.org

# Проверьте, не блокирует ли файрвол
```

### Ошибки загрузки

#### Проблема: "Failed to download video"

1. Проверьте, что FFmpeg установлен:
   ```bash
   ffmpeg -version
   ```

2. Проверьте доступ к YouTube:
   ```bash
   curl -I https://www.youtube.com
   ```

3. Обновите yt-dlp:
   ```bash
   pip install --upgrade yt-dlp
   ```

#### Проблема: "Storage disconnected"

1. Проверьте подключение к WebDAV:
   ```bash
   # Используйте команду /status в боте
   ```

2. Проверьте учетные данные WebDAV

3. Проверьте доступность WebDAV сервера:
   ```bash
   curl -I https://your-webdav-server.com
   ```

### Высокое использование памяти

```bash
# Уменьшите количество параллельных загрузок в .env
MAX_CONCURRENT_DOWNLOADS=1

# Перезапустите бота
sudo systemctl restart cloudtube  # Linux
# Или Ctrl+C и запустите снова
```

### База данных повреждена

```bash
# Создайте резервную копию
cp data/bot.db data/bot.db.backup

# Проверьте целостность
sqlite3 data/bot.db "PRAGMA integrity_check;"

# Если повреждена, восстановите из резервной копии
# или удалите и создайте новую:
rm data/bot.db
python -m bot.main  # База создастся автоматически
```

---

## Дополнительная помощь

### Документация

- [README.md](README.md) - Общая информация
- [WINDOWS_INSTALL.md](WINDOWS_INSTALL.md) - Установка на Windows
- [.env.example](.env.example) - Пример конфигурации

### Поддержка

Если у вас возникли проблемы:

1. Проверьте [Issues](https://github.com/brenli/CloudTube/issues)
2. Создайте новый Issue с описанием проблемы
3. Приложите логи и конфигурацию (без токенов!)

### Полезные команды

```bash
# Проверка версии Python
python --version

# Проверка установленных пакетов
pip list

# Проверка использования памяти
free -h  # Linux
Get-Process python | Select-Object WorkingSet  # Windows

# Проверка использования диска
df -h  # Linux
Get-PSDrive  # Windows

# Очистка временных файлов
rm -rf temp/*  # Linux
Remove-Item temp\* -Recurse  # Windows
```

---

## Готово! 🎉

Теперь ваш CloudTube установлен и готов к работе!

Следующие шаги:
1. Подключитесь к WebDAV: `/connect <url> <username> <password>`
2. Отправьте ссылку на видео YouTube
3. Наслаждайтесь автоматической загрузкой!

---

## 📦 Подключение к Yandex.Disk

Яндекс.Диск поддерживает WebDAV, но требует **пароль приложения** вместо основного пароля.

### Получение пароля приложения:

1. Перейдите на https://id.yandex.ru/security/app-passwords
2. Нажмите **"Создать пароль приложения"**
3. Выберите тип **"Файлы"** или **"WebDAV"**
4. Скопируйте сгенерированный пароль (показывается только один раз!)

### Подключение в боте:

```
/connect https://webdav.yandex.ru ваш_email@yandex.ru пароль_приложения
```

**Пример:**
```
/connect https://webdav.yandex.ru ivan@yandex.ru abcd1234efgh5678
```

### Важно:
- ❌ НЕ используйте основной пароль от аккаунта
- ✅ Используйте пароль приложения с типом "Файлы"
- 🔒 Пароль приложения можно отозвать в любой момент
- 📁 Файлы будут сохраняться в корень Яндекс.Диска

### Проверка подключения:

После команды `/connect` используйте:
```
/status
```

Вы должны увидеть:
```
✅ WebDAV: Подключено
💾 Место: X.XX GB свободно из Y.YY GB
```
