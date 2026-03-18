# Исправление проблемы с проверкой прав

## Что было не так

Код проверял права на запись в `/mnt/cloud_tube` ДО монтирования. Но:
- До монтирования директория может принадлежать root
- После монтирования права определяются опциями mount (uid/gid)

## Что исправлено

Теперь проверка прав происходит ПОСЛЕ монтирования:
1. Проверяется только существование mount point
2. Выполняется монтирование с опциями uid/gid
3. ПОСЛЕ монтирования проверяются права на запись

## Применение исправления

```bash
chmod +x quick_update.sh
sudo ./quick_update.sh
```

Или вручную:

```bash
# Остановить сервис
sudo systemctl stop cloudtube

# Обновить код
sudo cp bot/webdav.py /opt/CloudTube/bot/webdav.py

# Убедиться что mount point существует (права не важны)
sudo mkdir -p /mnt/cloud_tube

# Запустить сервис
sudo systemctl start cloudtube

# Смотреть логи
sudo journalctl -u cloudtube -f
```

## Что должно быть в логах

```
✅ Mount point /mnt/cloud_tube exists
✅ Using davfs2 directory: /home/cloudtube/.davfs2
✅ Mounting as user: cloudtube (uid=..., gid=...)
✅ WebDAV mounted successfully at /mnt/cloud_tube
✅ Write permissions verified on /mnt/cloud_tube
```

## Если монтирование не работает

Проверьте sudoers:

```bash
sudo -l -U cloudtube | grep mount
```

Если нет разрешений, установите:

```bash
sudo cp cloudtube-sudoers /etc/sudoers.d/cloudtube
sudo chmod 440 /etc/sudoers.d/cloudtube
sudo visudo -c
```

## Если все еще нет прав после монтирования

Проверьте что mount выполнен с правильными опциями:

```bash
mount | grep cloud_tube
```

Должно быть:
```
https://webdav.yandex.ru on /mnt/cloud_tube type fuse (rw,...,uid=XXX,gid=XXX,...)
```

Где XXX - это uid/gid пользователя cloudtube.
