# Исправление: Блокирующие вызовы yt-dlp в асинхронном коде

## Проблема

При отправке видео на загрузку задача создавалась успешно, но завершалась с ошибкой. Видео не загружалось.

### Причина

**yt-dlp** - это синхронная (блокирующая) библиотека, которая вызывалась напрямую в асинхронных функциях:

```python
# ❌ НЕПРАВИЛЬНО - блокирует event loop
async def download_video(self, url: str, ...):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)  # Блокирующий вызов!
```

Это приводило к:
- Блокировке event loop
- Таймаутам
- Зависанию других асинхронных операций
- Невозможности обработки других задач

## Решение

### 1. Асинхронное выполнение yt-dlp

Все вызовы yt-dlp теперь выполняются в отдельном потоке через `asyncio.run_in_executor()`:

```python
# ✅ ПРАВИЛЬНО - не блокирует event loop
async def download_video(self, url: str, ...):
    def _download_sync():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return filename
    
    # Выполняем в отдельном потоке
    loop = asyncio.get_event_loop()
    filename = await loop.run_in_executor(None, _download_sync)
    return filename
```

### 2. Правильное логирование

Заменены все `print()` на `logger.info()` / `logger.error()`:

```python
# ❌ НЕПРАВИЛЬНО - print() не работает в executor threads
print(f"[DEBUG] Starting download...")

# ✅ ПРАВИЛЬНО - logger работает везде
logger.info("Starting download...")
```

## Исправленные методы

1. **DownloadService.get_video_metadata()** - извлечение метаданных видео
2. **DownloadService.get_playlist_metadata()** - извлечение метаданных плейлиста
3. **TaskExecutor.download_video()** - загрузка видео
4. **TaskExecutor.execute_download()** - retry логика
5. **TaskQueue._process_task()** - обработка задач
6. **TaskQueue._worker()** - worker threads

## Применение исправлений

1. **Скопируйте файл** `bot/download.py` на продакшн сервер
2. **Перезапустите бота**:
   ```bash
   sudo systemctl restart cloudtube
   ```
3. **Проверьте логи**:
   ```bash
   sudo journalctl -u cloudtube -f
   ```

## Тестирование

После применения исправлений:

1. Отправьте тестовое видео на загрузку
2. Проверьте логи - должны появиться сообщения:
   ```
   INFO - Starting download for task {task_id}
   INFO - Attempt 1/3 for task {task_id}
   INFO - Submitting download to thread pool
   INFO - Starting yt-dlp download for URL: ...
   INFO - yt-dlp extraction completed
   INFO - Downloaded file size: ... bytes
   INFO - Thread pool execution completed: ...
   INFO - Download successful on attempt 1
   INFO - Download completed. Local path: ...
   INFO - Starting WebDAV upload...
   INFO - WebDAV upload completed successfully
   ```

3. Проверьте через `/history` - статус должен быть "completed"
4. Проверьте WebDAV хранилище - файл должен появиться

## Диагностика проблем

Если загрузка все еще не работает:

```bash
# Проверьте логи с ошибками
sudo journalctl -u cloudtube | grep ERROR

# Проверьте временную папку
ls -lh /opt/CloudTube/temp/

# Проверьте процессы
ps aux | grep python

# Проверьте использование диска
df -h
```

## Дата исправления

2026-03-15 (обновлено: добавлено правильное логирование)
