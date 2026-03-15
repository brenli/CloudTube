# Применение исправлений

## Что исправлено

1. ✅ yt-dlp теперь работает в отдельном потоке (не блокирует event loop)
2. ✅ WebDAV upload использует библиотеку `requests` для лучшей совместимости с Yandex.Disk
3. ✅ Увеличены таймауты для больших файлов (30 минут)
4. ✅ Добавлено подробное логирование

## Команды для применения

```bash
# На сервере выполните:

# 1. Перейдите в директорию проекта
cd /opt/CloudTube

# 2. Активируйте виртуальное окружение
source venv/bin/activate

# 3. Установите библиотеку requests
pip install requests==2.31.0

# 4. Перезапустите бота
sudo systemctl restart cloudtube

# 5. Проверьте что бот запустился
sudo systemctl status cloudtube

# 6. Следите за логами
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
INFO - Reading file into memory...
INFO - File read complete, starting upload...
INFO - Upload response status: 201
INFO - Upload completed successfully
```

## Если что-то не работает

```bash
# Проверьте что requests установлен
pip list | grep requests

# Проверьте логи на ошибки
sudo journalctl -u cloudtube | grep ERROR

# Проверьте что бот запущен
sudo systemctl status cloudtube

# Перезапустите если нужно
sudo systemctl restart cloudtube
```
