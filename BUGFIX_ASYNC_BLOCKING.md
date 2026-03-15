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

## Исправленные методы

1. **DownloadService.get_video_metadata()** - извлечение метаданных видео
2. **DownloadService.get_playlist_metadata()** - извлечение метаданных плейлиста
3. **TaskExecutor.download_video()** - загрузка видео

## Дополнительные улучшения

Добавлено подробное логирование для диагностики:
- Логи попыток загрузки с retry
- Логи работы yt-dlp
- Логи размера файлов
- Полный traceback при ошибках

## Тестирование

После применения исправлений:

1. Перезапустите бота на продакшн сервере
2. Отправьте тестовое видео на загрузку
3. Проверьте логи - должны появиться DEBUG сообщения:
   ```
   [DEBUG] Starting download for task {task_id}
   [DEBUG] Attempt 1/3 for task {task_id}
   [DEBUG] Starting yt-dlp download for URL: ...
   [DEBUG] Downloaded file size: ... bytes
   [DEBUG] Download completed. Local path: ...
   [DEBUG] Starting WebDAV upload...
   [DEBUG] WebDAV upload completed successfully
   ```

4. Проверьте через `/history` - статус должен быть "completed"

## Проверка на продакшн

```bash
# Перезапустите бота
sudo systemctl restart cloudtube

# Проверьте логи
sudo journalctl -u cloudtube -f

# Или если логи в файле
tail -f /opt/CloudTube/logs/bot.log
```

## Дата исправления

2026-03-15
