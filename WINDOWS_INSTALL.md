# 🪟 Установка на Windows

## Пошаговая инструкция для Windows 10/11

### Шаг 1: Установка Python

1. Перейдите на [python.org/downloads](https://www.python.org/downloads/)
2. Скачайте **Python 3.11** или новее
3. Запустите установщик
4. ✅ **ВАЖНО**: Поставьте галочку **"Add Python to PATH"**
5. Нажмите **"Install Now"**
6. Дождитесь завершения установки

**Проверка установки:**
```powershell
python --version
# Должно показать: Python 3.11.x или выше
```

---

### Шаг 2: Установка FFmpeg

FFmpeg нужен для обработки видео.

#### Вариант A: Через Chocolatey (рекомендуется)

1. Установите Chocolatey (если еще не установлен):
   - Откройте PowerShell **от имени администратора**
   - Выполните:
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```

2. Установите FFmpeg:
   ```powershell
   choco install ffmpeg
   ```

#### Вариант B: Ручная установка

1. Скачайте FFmpeg с [ffmpeg.org/download.html](https://ffmpeg.org/download.html)
   - Выберите "Windows builds from gyan.dev"
   - Скачайте "ffmpeg-release-essentials.zip"

2. Распакуйте архив в `C:\ffmpeg`

3. Добавьте в PATH:
   - Нажмите `Win + X` → "Система"
   - "Дополнительные параметры системы"
   - "Переменные среды"
   - В разделе "Системные переменные" найдите "Path"
   - Нажмите "Изменить"
   - Нажмите "Создать"
   - Добавьте: `C:\ffmpeg\bin`
   - Нажмите "ОК" везде

4. **Перезапустите PowerShell**

**Проверка установки:**
```powershell
ffmpeg -version
# Должно показать версию FFmpeg
```

---

### Шаг 3: Установка Git (если еще не установлен)

1. Скачайте Git с [git-scm.com](https://git-scm.com/download/win)
2. Запустите установщик
3. Используйте настройки по умолчанию

**Проверка:**
```powershell
git --version
```

---

### Шаг 4: Клонирование проекта

```powershell
# Создайте папку для проектов (если еще нет)
mkdir C:\Projects
cd C:\Projects

# Клонируйте репозиторий
git clone https://github.com/brenli/CloudTube.git
cd CloudTube
```

---

### Шаг 5: Автоматическая установка

```powershell
# Запустите скрипт установки
.\setup.bat
```

Скрипт автоматически:
- ✅ Проверит Python и FFmpeg
- ✅ Создаст виртуальное окружение
- ✅ Установит все зависимости
- ✅ Создаст папки `data`, `logs`, `temp`
- ✅ Создаст файл `.env` из шаблона
- ✅ Откроет `.env` в Блокноте для редактирования

---

### Шаг 6: Настройка Telegram бота

#### 6.1. Создание бота

1. Откройте Telegram на телефоне или в браузере
2. Найдите [@BotFather](https://t.me/BotFather)
3. Отправьте команду: `/newbot`
4. Введите имя бота (например: "My YouTube Downloader")
5. Введите username бота (должен заканчиваться на "bot", например: "my_youtube_dl_bot")
6. **Скопируйте токен** (выглядит как `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

#### 6.2. Получение вашего ID

1. Найдите [@userinfobot](https://t.me/userinfobot)
2. Отправьте команду: `/start`
3. **Скопируйте ваш ID** (число, например: `123456789`)

#### 6.3. Заполнение конфигурации

Откройте файл `.env` (должен был открыться автоматически, если нет - откройте вручную):

```powershell
notepad .env
```

Заполните:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_OWNER_ID=123456789
```

Сохраните файл (`Ctrl+S`) и закройте Блокнот.

---

### Шаг 7: Запуск бота

```powershell
# Активируйте виртуальное окружение
.\venv\Scripts\Activate.ps1

# Если появится ошибка про ExecutionPolicy, выполните:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Запустите бота
python -m bot.main
```

Вы должны увидеть:
```
2026-03-14 12:00:00 - root - INFO - Logging initialized
2026-03-14 12:00:00 - root - CRITICAL - Bot starting
2026-03-14 12:00:00 - root - CRITICAL - Bot started successfully
```

**Бот запущен!** 🎉

---

### Шаг 8: Проверка работы

1. Откройте Telegram
2. Найдите вашего бота по username
3. Отправьте команду: `/start`
4. Вы должны получить приветственное сообщение

---

## 🎯 Первое использование

### 1. Подключение к WebDAV

```
/connect https://webdav.example.com username password
```

Замените на ваши данные WebDAV хранилища.

### 2. Загрузка видео

Просто отправьте ссылку на YouTube видео:
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

Бот предложит:
1. Выбрать качество (best, 1080p, 720p, 480p, 360p)
2. Настроить уведомления

### 3. Загрузка плейлиста

Отправьте ссылку на плейлист:
```
https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf
```

---

## 📋 Полезные команды

### Управление ботом

```powershell
# Запуск бота
.\venv\Scripts\Activate.ps1
python -m bot.main

# Остановка бота
# Нажмите Ctrl+C в окне PowerShell

# Просмотр логов
Get-Content logs\bot.log -Tail 50

# Просмотр логов в реальном времени
Get-Content logs\bot.log -Wait
```

### Команды бота в Telegram

- `/start` - Приветствие и список команд
- `/help` - Подробная справка
- `/status` - Статус системы
- `/history` - История загрузок
- `/cancel <task_id>` - Отменить загрузку
- `/pause <task_id>` - Приостановить загрузку
- `/resume <task_id>` - Возобновить загрузку
- `/connect <url> <user> <pass>` - Подключиться к WebDAV

---

## 🔧 Автозапуск при старте Windows

### Вариант 1: Через Task Scheduler (рекомендуется)

1. Откройте "Планировщик заданий" (`Win + R` → `taskschd.msc`)
2. Нажмите "Создать задачу..."
3. **Общие:**
   - Имя: "CloudTube"
   - Выполнять для всех пользователей
   - Выполнять с наивысшими правами
4. **Триггеры:**
   - Создать → При входе в систему
5. **Действия:**
   - Создать → Запуск программы
   - Программа: `C:\Projects\CloudTube\venv\Scripts\python.exe`
   - Аргументы: `-m bot.main`
   - Рабочая папка: `C:\Projects\CloudTube`
6. **Условия:**
   - Снять галочку "Запускать только при питании от сети"
7. Нажмите "ОК"

### Вариант 2: Через папку автозагрузки

Создайте файл `start_bot.bat`:
```batch
@echo off
cd C:\Projects\CloudTube
call venv\Scripts\activate.bat
python -m bot.main
```

Поместите ярлык на этот файл в:
```
C:\Users\ВашеИмя\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
```

---

## 🆘 Устранение проблем

### Проблема: "python не является внутренней командой"

**Решение:**
1. Переустановите Python с галочкой "Add Python to PATH"
2. Или добавьте Python в PATH вручную:
   - Найдите путь к Python (обычно `C:\Users\ВашеИмя\AppData\Local\Programs\Python\Python311`)
   - Добавьте в PATH (см. инструкцию для FFmpeg)

### Проблема: "ffmpeg не является внутренней командой"

**Решение:**
1. Проверьте установку FFmpeg (см. Шаг 2)
2. Убедитесь, что `C:\ffmpeg\bin` добавлен в PATH
3. Перезапустите PowerShell

### Проблема: "Не удается загрузить файл... ExecutionPolicy"

**Решение:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Проблема: Бот не отвечает в Telegram

**Проверка:**
1. Убедитесь, что бот запущен (окно PowerShell открыто)
2. Проверьте токен в `.env`
3. Проверьте логи:
   ```powershell
   Get-Content logs\bot.log -Tail 50
   ```

### Проблема: "ModuleNotFoundError"

**Решение:**
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Проблема: Высокое использование памяти

**Решение:**
Отредактируйте `.env`:
```env
MAX_CONCURRENT_DOWNLOADS=1
```

---

## 📊 Мониторинг

### Просмотр использования ресурсов

```powershell
# Использование памяти
Get-Process python | Select-Object WorkingSet, CPU

# Использование диска
Get-PSDrive C
```

### Очистка временных файлов

```powershell
Remove-Item temp\* -Recurse -Force
```

---

## 🔄 Обновление

```powershell
cd C:\Projects\CloudTube

# Остановите бота (Ctrl+C)

# Обновите код
git pull

# Активируйте venv
.\venv\Scripts\Activate.ps1

# Обновите зависимости
pip install -r requirements.txt --upgrade

# Запустите бота
python -m bot.main
```

---

## ✅ Готово!

Теперь ваш CloudTube работает на Windows!

**Следующие шаги:**
1. Подключитесь к WebDAV: `/connect <url> <user> <pass>`
2. Отправьте ссылку на YouTube видео
3. Наслаждайтесь автоматической загрузкой! 🎉

**Нужна помощь?**
- [INSTALLATION.md](INSTALLATION.md) - Полная документация
- [README.md](README.md) - Общая информация
- [Issues](https://github.com/brenli/CloudTube/issues) - Сообщить о проблеме
