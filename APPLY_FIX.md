# Применение исправлений

## Что исправлено

1. ✅ yt-dlp теперь работает в отдельном потоке (не блокирует event loop)
2. ✅ WebDAV upload использует `curl` вместо Python библиотек (решает проблему timeout)
3. ✅ Увеличены таймауты для больших файлов (1 час)
4. ✅ Добавлено подробное логирование

## Почему curl?

Python библиотеки (httpx, requests) имеют проблемы с socket write timeout при загрузке больших файлов. Curl:
- Правильно работает с WebDAV и Yandex.Disk
- Не имеет проблем с таймаутами
- Эффективно загружает файлы любого размера
- Уже установлен на всех Linux серверах

## Команды для применения

```bash
# На сервере выполните:

# 1. Перейдите в директорию проекта
cd /opt/CloudTube

# 2. Убедитесь что curl установлен (обычно уже есть)
curl --version

# 3. Перезапустите бота
sudo systemctl restart cloudtube

# 4. Проверьте что бот запустился
sudo systemctl status cloudtube

# 5. Следите за логами
sudo journalctl -u cloudtube -f
```

## Тестирование

После применения исправлений:

1. Отправьте боту короткое видео (< 50 MB)
2. Проверьте логи - должны появиться сообщения о загрузке и upload
3. Проверьте `/history` - статус должен быть "completed"
4. Проверьте Yandex.Disk - файл должен быть в папке "Single Videos"

## Ожидаемые логи при успешной загрузке

```
INFO - Starting download for task ...
INFO - Submitting download to thread pool
[youtube] Extracting URL: ...
[download] 100% of 96.9MiB in 00:05
INFO - Downloaded file size: 120247586 bytes
INFO - Starting WebDAV upload...
INFO - Uploading file: ... (120247586 bytes / 114.7 MB)
INFO - Uploading using curl...
INFO - Curl completed with status: 201
INFO - Upload completed successfully
```

## Если что-то не работает

```bash
# Проверьте что curl установлен
curl --version

# Если curl не установлен (редко):
sudo apt-get install curl  # Debian/Ubuntu
sudo yum install curl      # CentOS/RHEL

# Проверьте логи на ошибки
sudo journalctl -u cloudtube | grep ERROR

# Проверьте что бот запущен
sudo systemctl status cloudtube

# Перезапустите если нужно
sudo systemctl restart cloudtube
```
