# Применение изменений

## ⚠️ ВАЖНО: Код на сервере устарел!

Ошибка показывает, что на сервере запущена старая версия кода. Нужно применить изменения.

## Быстрое решение

```bash
# На сервере выполните:
chmod +x deploy_changes.sh
sudo ./deploy_changes.sh
```

Этот скрипт:
1. Остановит сервис
2. Скопирует новый код на сервер
3. Создаст все необходимые директории
4. Установит правильные права
5. Перезапустит сервис

## Альтернативный способ (вручную)

Если скрипт не работает, выполните команды вручную:

```bash
# 1. Остановить сервис
sudo systemctl stop cloudtube

# 2. Скопировать новый код (если вы в директории проекта)
sudo cp bot/webdav.py /opt/CloudTube/bot/webdav.py
sudo chown cloudtube:cloudtube /opt/CloudTube/bot/webdav.py

# 3. Обновить systemd конфигурацию
sudo cp systemd/cloudtube.service /etc/systemd/system/cloudtube.service
sudo systemctl daemon-reload

# 4. Создать директории
sudo mkdir -p /home/cloudtube/.davfs2
sudo chown cloudtube:cloudtube /home/cloudtube/.davfs2
sudo chmod 700 /home/cloudtube/.davfs2

sudo mkdir -p /mnt/cloud_tube
sudo chown cloudtube:cloudtube /mnt/cloud_tube
sudo chmod 755 /mnt/cloud_tube

# 5. Запустить сервис
sudo systemctl start cloudtube

# 6. Проверить логи
sudo journalctl -u cloudtube -f
```

## Проверка результата

После применения изменений в логах должно быть:

```
Using davfs2 directory: /home/cloudtube/.davfs2
Creating mount point /mnt/cloud_tube
```

А НЕ:
```
Using davfs2 directory: /opt/CloudTube/.davfs2  ❌
```

## Если все еще ошибка

Проверьте, что файл действительно обновлен:

```bash
# Проверить дату изменения файла
ls -l /opt/CloudTube/bot/webdav.py

# Проверить содержимое (должно быть /mnt/cloud_tube)
grep "MOUNT_POINT" /opt/CloudTube/bot/webdav.py

# Должно вывести:
# MOUNT_POINT = "/mnt/cloud_tube"
```
