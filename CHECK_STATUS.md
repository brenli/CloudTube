# Проверка статуса загрузки

## Текущее состояние

✅ Загрузка ЗАПУСТИЛАСЬ успешно!

Из логов видно:
- Task ID: `7fd00102-3b32-4e5e-98c8-8cbe8d5425b7`
- URL: `https://youtu.be/ABQvgv5SUhg?si=U1dOigmtzrtpfR_4`
- Статус: Загрузка началась, yt-dlp работает

## Что нужно проверить

### 1. Дождитесь завершения загрузки

Видео загружается, это может занять несколько минут в зависимости от:
- Размера видео
- Качества (best, 1080p, 720p, etc.)
- Скорости интернета

### 2. Проверьте полные логи

```bash
# Смотрите логи в реальном времени
sudo journalctl -u cloudtube -f

# Или последние 100 строк
sudo journalctl -u cloudtube -n 100
```

### 3. Ожидаемые логи при успешной загрузке

```
[DEBUG] Starting yt-dlp download for URL: ...
[DEBUG] yt-dlp extraction completed
[DEBUG] Prepared filename: /path/to/file.mp4
[DEBUG] Downloaded file size: XXXXX bytes
[DEBUG] Thread pool execution completed: /path/to/file.mp4
[DEBUG] Download successful on attempt 1
[DEBUG] Download completed. Local path: /path/to/file.mp4
[DEBUG] File exists: True
[DEBUG] File size: XXXXX bytes
[DEBUG] Remote path: Single Videos/filename.mp4
[DEBUG] Starting WebDAV upload...
[DEBUG] WebDAV upload completed successfully
```

### 4. Проверьте статус через бота

Отправьте команду в Telegram:
```
/history
```

Должно показать:
- ✅ Статус: completed
- 📁 Путь: Single Videos/название_видео.mp4

### 5. Проверьте WebDAV хранилище

Зайдите в ваше WebDAV хранилище (Yandex.Disk) и проверьте папку "Single Videos" - там должен появиться загруженный файл.

## Если загрузка не завершается

### Возможные причины:

1. **Большой размер видео** - загрузка может занять 5-10 минут
2. **Медленный интернет** - проверьте скорость соединения
3. **Ошибка yt-dlp** - проверьте логи на наличие ошибок
4. **Проблема с WebDAV** - проверьте подключение к Yandex.Disk

### Команды для диагностики:

```bash
# Проверить процессы Python
ps aux | grep python

# Проверить использование диска
df -h

# Проверить временную папку
ls -lh /opt/CloudTube/temp/

# Проверить логи с ошибками
sudo journalctl -u cloudtube | grep ERROR
sudo journalctl -u cloudtube | grep FAILED
```

## Следующие шаги

1. ⏳ Подождите 2-3 минуты
2. 📋 Проверьте логи снова
3. 💬 Отправьте `/history` в боте
4. ✅ Проверьте файл в Yandex.Disk

Если через 5 минут загрузка не завершилась - пришлите полные логи для дальнейшей диагностики.
