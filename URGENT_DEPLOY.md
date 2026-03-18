# ⚠️ СРОЧНО: КОД НЕ ОБНОВЛЕН НА СЕРВЕРЕ

## Проблема
Логи показывают:
```
Creating mount point /mnt/cloud_tube
```

Это СТАРАЯ версия кода! Новая версия должна показывать:
```
Mount point /mnt/cloud_tube is ready
```

## Решение

### Вариант 1: Автоматический деплой

```bash
# На сервере в директории проекта выполните:
chmod +x deploy_changes.sh
sudo ./deploy_changes.sh
```

### Вариант 2: Ручное обновление (если скрипт не работает)

```bash
# 1. Остановить сервис
sudo systemctl stop cloudtube

# 2. Проверить что файл bot/webdav.py существует локально
ls -l bot/webdav.py

# 3. Скопировать новый код
sudo cp bot/webdav.py /opt/CloudTube/bot/webdav.py
sudo chown cloudtube:cloudtube /opt/CloudTube/bot/webdav.py

# 4. Проверить что файл обновлен
grep "Mount point .* is ready" /opt/CloudTube/bot/webdav.py

# Должно найти строку с "Mount point {MOUNT_POINT} is ready"

# 5. Установить sudoers
sudo cp cloudtube-sudoers /etc/sudoers.d/cloudtube
sudo chmod 440 /etc/sudoers.d/cloudtube
sudo visudo -c

# 6. Создать mount point
sudo mkdir -p /mnt/cloud_tube
sudo chown cloudtube:cloudtube /mnt/cloud_tube
sudo chmod 755 /mnt/cloud_tube

# 7. Создать .davfs2
sudo mkdir -p /home/cloudtube/.davfs2
sudo chown cloudtube:cloudtube /home/cloudtube/.davfs2
sudo chmod 700 /home/cloudtube/.davfs2

# 8. Запустить сервис
sudo systemctl start cloudtube

# 9. Смотреть логи
sudo journalctl -u cloudtube -f
```

## Проверка что код обновлен

```bash
# Проверить содержимое файла на сервере
grep -A 5 "Check if mount point exists" /opt/CloudTube/bot/webdav.py

# Должно показать новый код с проверкой существования
```

## Если вы НЕ на сервере

Если вы работаете локально и нужно загрузить изменения на сервер:

```bash
# Скопировать файлы на сервер (замените user@server на ваши данные)
scp bot/webdav.py user@server:/tmp/
scp cloudtube-sudoers user@server:/tmp/
scp deploy_changes.sh user@server:/tmp/

# Подключиться к серверу
ssh user@server

# На сервере
cd /tmp
chmod +x deploy_changes.sh
sudo ./deploy_changes.sh
```

## Что должно быть в логах после обновления

```
✅ Mount point /mnt/cloud_tube is ready
✅ Using davfs2 directory: /home/cloudtube/.davfs2
✅ Mounting as user: cloudtube (uid=..., gid=...)
✅ Mounting WebDAV: sudo mount -t davfs ...
```

А НЕ:
```
❌ Creating mount point /mnt/cloud_tube
❌ sudo: The "no new privileges" flag is set
```
