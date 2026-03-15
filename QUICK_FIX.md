# Быстрое исправление

## Проблема
WebDAV upload падает с `TimeoutError: The write operation timed out` через 30 секунд.

## Решение
Использовать `curl` вместо Python библиотек для загрузки на Yandex.Disk.

## Применить исправление

```bash
# На сервере:
cd /opt/CloudTube
sudo systemctl restart cloudtube
sudo journalctl -u cloudtube -f
```

Файлы `bot/download.py` и `bot/webdav.py` уже обновлены в репозитории.

## Что изменилось

- `bot/webdav.py` теперь использует `curl` для upload
- Таймаут увеличен до 1 часа
- Curl работает надежнее с Yandex.Disk WebDAV

## Проверка

После перезапуска отправьте тестовое видео боту. В логах должно быть:

```
INFO - Uploading using curl...
INFO - Curl completed with status: 201
INFO - Upload completed successfully
```

Файл должен появиться в Yandex.Disk в папке "Single Videos".
