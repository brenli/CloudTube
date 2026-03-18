# 🔥 СРОЧНОЕ ИСПРАВЛЕНИЕ

## Проблема
На сервере запущена **СТАРАЯ ВЕРСИЯ КОДА**!

Ошибка:
```
OSError: [Errno 30] Read-only file system: '/opt/CloudTube/.davfs2'
```

Это значит, что код на сервере все еще пытается использовать `/opt/CloudTube/.davfs2` вместо `/home/cloudtube/.davfs2`.

## Решение за 1 команду

```bash
chmod +x deploy_changes.sh && sudo ./deploy_changes.sh
```

Этот скрипт:
- ✅ Остановит сервис
- ✅ Скопирует новый код
- ✅ Создаст все директории
- ✅ Установит права
- ✅ Перезапустит сервис

## Проверка

После выполнения скрипта:

```bash
# Проверить что код обновлен
grep "MOUNT_POINT" /opt/CloudTube/bot/webdav.py

# Должно вывести:
# MOUNT_POINT = "/mnt/cloud_tube"

# Смотреть логи
sudo journalctl -u cloudtube -f
```

В логах должно быть:
```
✅ Using davfs2 directory: /home/cloudtube/.davfs2
✅ Creating mount point /mnt/cloud_tube
```

## Если скрипт не работает

Скопируйте файлы вручную:

```bash
# 1. Остановить сервис
sudo systemctl stop cloudtube

# 2. Обновить код (ВАЖНО!)
sudo cp bot/webdav.py /opt/CloudTube/bot/webdav.py
sudo chown cloudtube:cloudtube /opt/CloudTube/bot/webdav.py

# 3. Создать директории
sudo mkdir -p /home/cloudtube/.davfs2
sudo chown cloudtube:cloudtube /home/cloudtube/.davfs2
sudo chmod 700 /home/cloudtube/.davfs2

sudo mkdir -p /mnt/cloud_tube
sudo chown cloudtube:cloudtube /mnt/cloud_tube

# 4. Обновить systemd
sudo cp systemd/cloudtube.service /etc/systemd/system/cloudtube.service
sudo systemctl daemon-reload

# 5. Запустить
sudo systemctl start cloudtube
```

## Почему это произошло?

Код был изменен локально, но изменения не были применены на сервере в `/opt/CloudTube/`. Сервис продолжал использовать старую версию файла `bot/webdav.py`.
