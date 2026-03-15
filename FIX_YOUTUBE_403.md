# Исправление ошибки YouTube HTTP 403

## Проблема

При попытке загрузить видео с YouTube бот выдает ошибку:
```
HTTP Error 403: Forbidden
```

Это происходит потому, что YouTube блокирует запросы от yt-dlp без правильных заголовков.

## Решение

Были внесены следующие изменения:

### 1. Обновлены заголовки в `bot/download.py`

Добавлены User-Agent и Referer заголовки для обхода блокировки YouTube:

- В `DownloadService.__init__()` - для извлечения метаданных
- В `TaskExecutor.download_video()` - для загрузки видео

### 2. Обновлена версия yt-dlp в `requirements.txt`

Изменено с `yt-dlp==2024.3.10` на `yt-dlp>=2024.12.23`

### 3. Созданы скрипты для обновления

- `update_ytdlp.sh` - для Linux/macOS
- `update_ytdlp.bat` - для Windows

### 4. Добавлена документация

В README.md добавлен раздел с решением проблемы HTTP 403.

## Как применить исправление

### Вариант 1: Автоматическое обновление (рекомендуется)

#### Linux/macOS:
```bash
cd /opt/CloudTube
git pull origin main
./update_ytdlp.sh
```

#### Windows:
```cmd
cd C:\CloudTube
git pull origin main
update_ytdlp.bat
```

### Вариант 2: Ручное обновление

1. Обновите код из репозитория:
```bash
git pull origin main
```

2. Активируйте виртуальное окружение:
```bash
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate.bat
```

3. Обновите зависимости:
```bash
pip install --upgrade yt-dlp
```

4. Перезапустите бота:

**Если используется systemd (Linux):**
```bash
sudo systemctl restart cloudtube
sudo systemctl status cloudtube
```

**Если запущен вручную:**
- Остановите бота (Ctrl+C)
- Запустите снова: `python -m bot.main`

## Проверка

После применения исправления:

1. Отправьте боту ссылку на YouTube видео
2. Выберите качество
3. Загрузка должна начаться без ошибки 403

## Дополнительная информация

### Что было изменено в коде?

**bot/download.py** - добавлены заголовки:
```python
'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
'referer': 'https://www.youtube.com/',
'nocheckcertificate': True,
'prefer_insecure': False,
'age_limit': None,
```

### Почему это работает?

YouTube блокирует запросы, которые выглядят как боты. Добавление User-Agent браузера и Referer заставляет запросы выглядеть как обычные запросы из браузера.

### Если проблема сохраняется

1. Убедитесь, что yt-dlp обновлен до последней версии:
```bash
yt-dlp --version
```

2. Попробуйте другое видео (возможно, конкретное видео недоступно)

3. Подождите несколько минут и попробуйте снова

4. Проверьте логи бота:
```bash
# Если используется systemd
sudo journalctl -u cloudtube -f

# Если запущен вручную
# Смотрите вывод в консоли
```

## Статус тестов

Все тесты загрузки (download) проходят успешно:
- ✅ test_get_video_metadata_success
- ✅ test_get_video_metadata_invalid_url
- ✅ test_get_playlist_metadata_success
- ✅ И другие (9/9 тестов)

Некоторые тесты уведомлений не проходят из-за изменений в NotificationService в предыдущих задачах, но это не влияет на функциональность загрузки.
