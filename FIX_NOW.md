# 🔥 СРОЧНОЕ ИСПРАВЛЕНИЕ

## Новая проблема
```
sudo: The "no new privileges" flag is set, which prevents sudo from running as root.
```

`NoNewPrivileges=true` в systemd блокирует sudo внутри процесса.

## Решение

Нужно дать пользователю `cloudtube` права на mount/umount без пароля через sudoers.

### Автоматическое исправление

```bash
chmod +x deploy_changes.sh
sudo ./deploy_changes.sh
```

Скрипт:
- ✅ Установит sudoers правила для cloudtube
- ✅ Создаст все директории
- ✅ Обновит код
- ✅ Перезапустит сервис

### Ручное исправление

Если скрипт не работает:

```bash
# 1. Остановить сервис
sudo systemctl stop cloudtube

# 2. Установить sudoers правила
sudo cp cloudtube-sudoers /etc/sudoers.d/cloudtube
sudo chmod 440 /etc/sudoers.d/cloudtube

# 3. Проверить синтаксис sudoers
sudo visudo -c

# 4. Создать директории
sudo mkdir -p /home/cloudtube/.davfs2
sudo chown cloudtube:cloudtube /home/cloudtube/.davfs2
sudo chmod 700 /home/cloudtube/.davfs2

sudo mkdir -p /mnt/cloud_tube
sudo chown cloudtube:cloudtube /mnt/cloud_tube
sudo chmod 755 /mnt/cloud_tube

# 5. Обновить код
sudo cp bot/webdav.py /opt/CloudTube/bot/webdav.py
sudo chown cloudtube:cloudtube /opt/CloudTube/bot/webdav.py

# 6. Обновить systemd
sudo cp systemd/cloudtube.service /etc/systemd/system/cloudtube.service
sudo systemctl daemon-reload

# 7. Запустить
sudo systemctl start cloudtube
```

## Проверка

```bash
# Проверить sudoers
sudo -l -U cloudtube

# Должно показать разрешенные команды mount/umount

# Смотреть логи
sudo journalctl -u cloudtube -f
```

В логах должно быть:
```
✅ Mount point /mnt/cloud_tube is ready
✅ Mounting WebDAV...
✅ WebDAV mounted successfully
```

## Что делает sudoers конфигурация

Файл `/etc/sudoers.d/cloudtube` разрешает пользователю `cloudtube` выполнять БЕЗ ПАРОЛЯ:
- `mount -t davfs` в `/mnt/cloud_tube`
- `umount /mnt/cloud_tube`
- Создание и настройку mount point (для первого запуска)

Это безопасно, так как разрешены только конкретные команды для конкретной директории.
