# Финальное исправление: Загрузка видео зависает

## Проблема

Логи показывают, что yt-dlp запускается, но затем зависает без вывода ошибок:
```
INFO - Submitting download to thread pool
INFO - Starting yt-dlp download for URL: ...
INFO - Quality: best, Output: ./temp/download_...
[2.7k blob data]  <-- Зависает здесь
```

## Причины

1. **yt-dlp работает в quiet mode** - ошибки не видны
2. **Нет таймаута** - зависший download блокирует поток навсегда
3. **Нет обработки исключений** в executor thread
4. **YouTube может блокировать** - нужны дополнительные опции

## Решение

### 1. Включен verbose режим yt-dlp

```python
ydl_opts = {
    'quiet': False,        # Показывать вывод
    'no_warnings': False,  # Показывать предупреждения
    'verbose': True,       # Подробный вывод
    ...
}
```

### 2. Добавлен таймаут 30 минут

```python
filename = await asyncio.wait_for(
    loop.run_in_executor(None, _download_sync),
    timeout=1800.0  # 30 минут
)
```

### 3. Добавлены retry и socket timeout

```python
ydl_opts = {
    'retries': 10,
    'fragment_retries': 10,
    'socket_timeout': 30,
    ...
}
```

### 4. Обработка исключений в thread

```python
def _download_sync():
    try:
        # ... download code ...
    except Exception as e:
        logger.error(f"Error in _download_sync: {str(e)}", exc_info=True)
        raise
```

## Применение

1. **Скопируйте файл** на продакшн:
   ```bash
   scp bot/download.py user@server:/opt/CloudTube/bot/
   ```

2. **Перезапустите бота**:
   ```bash
   sudo systemctl restart cloudtube
   ```

3. **Отправьте тестовое видео**

4. **Смотрите логи**:
   ```bash
   sudo journalctl -u cloudtube -f
   ```

## Ожидаемые логи

Теперь вы увидите ПОЛНЫЙ вывод yt-dlp:

```
INFO - Starting yt-dlp download for URL: ...
INFO - Quality: best, Output: ./temp/download_...
INFO - Extracting video info...
[youtube] Extracting URL: https://youtu.be/...
[youtube] Video ID: ...
[youtube] Downloading webpage
[youtube] Downloading android player API JSON
[info] Available formats for ...
[download] Destination: /temp/download_...
[download] 100% of 15.5MiB in 00:05
[Merger] Merging formats into "/temp/download_....mp4"
INFO - yt-dlp extraction completed
INFO - Prepared filename: /temp/download_....mp4
INFO - Downloaded file size: 16234567 bytes
INFO - Thread pool execution completed: /temp/download_....mp4
```

## Если все еще не работает

### Проверьте ошибки yt-dlp:

```bash
# Проверьте логи на ошибки
sudo journalctl -u cloudtube | grep -A 10 "ERROR"

# Проверьте, есть ли файлы в temp
ls -lh /opt/CloudTube/temp/

# Попробуйте загрузить вручную
cd /opt/CloudTube
source venv/bin/activate
yt-dlp -v "https://youtu.be/VIDEO_ID"
```

### Возможные проблемы:

1. **YouTube блокирует IP** - попробуйте другое видео
2. **Нет места на диске** - проверьте `df -h`
3. **Нет ffmpeg** - установите `sudo apt install ffmpeg`
4. **Старая версия yt-dlp** - обновите `pip install -U yt-dlp`

### Обновление yt-dlp:

```bash
cd /opt/CloudTube
source venv/bin/activate
pip install -U yt-dlp
sudo systemctl restart cloudtube
```

## Дата исправления

2026-03-15 (финальная версия с verbose logging и timeout)
