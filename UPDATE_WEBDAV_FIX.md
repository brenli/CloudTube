# Исправление проблемы с davfs2

## Проблема

При попытке подключения к Яндекс.Диску возникает ошибка:
```
Failed to setup davfs2: [Errno 30] Read-only file system: '/opt/CloudTube/.davfs2'
```

## Причина

Systemd сервис с настройками `ProtectHome=true` блокирует доступ к домашней директории пользователя, где должны храниться конфигурационные файлы davfs2.

## Решение

### Шаг 1: Остановите бота

```bash
sudo systemctl stop cloudtube
```

### Шаг 2: Обновите код

```bash
cd /opt/CloudTube
git pull origin main
```

Или скопируйте обновленные файлы:
- `bot/webdav.py`
- `systemd/cloudtube.service`

### Шаг 3: Создайте домашнюю директорию для пользователя

```bash
# Узнайте под каким пользователем запущен сервис
SERVICE_USER=$(grep "^User=" /etc/systemd/system/cloudtube.service | cut -d'=' -f2)
echo "Service user: $SERVICE_USER"

# Создайте домашнюю директорию
sudo mkdir -p "/home/$SERVICE_USER"
sudo chown $SERVICE_USER:$SERVICE_USER "/home/$SERVICE_USER"

# Создайте директорию для davfs2
sudo mkdir -p "/home/$SERVICE_USER/.davfs2"
sudo chown $SERVICE_USER:$SERVICE_USER "/home/$SERVICE_USER/.davfs2"
```

### Шаг 4: Создайте конфигурацию davfs2

```bash
SERVICE_USER=$(grep "^User=" /etc/systemd/system/cloudtube.service | cut -d'=' -f2)

sudo tee "/home/$SERVICE_USER/.davfs2/davfs2.conf" > /dev/null << 'EOF'
# davfs2 configuration
use_locks 0
cache_size 50
delay_upload 0
EOF

sudo chown $SERVICE_USER:$SERVICE_USER "/home/$SERVICE_USER/.davfs2/davfs2.conf"
```

### Шаг 5: Обновите systemd сервис

```bash
# Скопируйте обновленный файл сервиса
sudo cp /opt/CloudTube/systemd/cloudtube.service /etc/systemd/system/

# Или отредактируйте вручную
sudo nano /etc/systemd/system/cloudtube.service
```

Убедитесь, что в файле есть:

```ini
[Service]
# ... другие настройки ...
Environment="HOME=/home/cloudtube"  # или ваш пользователь
ProtectHome=false  # ВАЖНО: было true
ReadWritePaths=/opt/CloudTube/data /opt/CloudTube/logs /opt/CloudTube/temp /home/cloudtube/.davfs2 /mnt/yandex-disk
```

Замените `cloudtube` на вашего пользователя, если используется другой.

### Шаг 6: Перезагрузите systemd и запустите бота

```bash
sudo systemctl daemon-reload
sudo systemctl start cloudtube
```

### Шаг 7: Проверьте статус

```bash
sudo systemctl status cloudtube
```

Должно показать `active (running)` без ошибок.

### Шаг 8: Проверьте логи

```bash
sudo journalctl -u cloudtube -f
```

Теперь при выполнении `/connect` не должно быть ошибок с файловой системой.

## Проверка работы

1. Откройте Telegram и напишите боту:
   ```
   /connect https://webdav.yandex.ru ваш_email@yandex.ru ваш_oauth_токен
   ```

2. Бот должен ответить:
   ```
   ✅ Успешно подключено к Yandex.Disk
   💾 Конфигурация сохранена
   ```

3. Проверьте, что файлы созданы:
   ```bash
   SERVICE_USER=$(grep "^User=" /etc/systemd/system/cloudtube.service | cut -d'=' -f2)
   sudo ls -la "/home/$SERVICE_USER/.davfs2/"
   ```

   Должны быть файлы:
   - `davfs2.conf`
   - `secrets` (после выполнения /connect)

4. Проверьте монтирование:
   ```bash
   mount | grep yandex-disk
   ```

   Должна быть строка вида:
   ```
   https://webdav.yandex.ru on /mnt/yandex-disk type fuse.davfs2 (...)
   ```

## Альтернативное решение (без systemd)

Если вы запускаете бота вручную (не через systemd):

```bash
cd /opt/CloudTube
source venv/bin/activate

# Убедитесь, что HOME установлен правильно
export HOME=/home/ваш_пользователь

python -m bot.main
```

## Устранение проблем

### Ошибка: "Permission denied" при создании .davfs2

```bash
# Проверьте владельца домашней директории
SERVICE_USER=$(grep "^User=" /etc/systemd/system/cloudtube.service | cut -d'=' -f2)
ls -la /home/ | grep $SERVICE_USER

# Если директории нет или неправильный владелец
sudo mkdir -p "/home/$SERVICE_USER"
sudo chown -R $SERVICE_USER:$SERVICE_USER "/home/$SERVICE_USER"
```

### Ошибка: "mount.davfs: mounting failed"

Это другая проблема, связанная с учетными данными. См. [YANDEX_DISK_SETUP.md](YANDEX_DISK_SETUP.md)

### Проверка переменных окружения

```bash
# Посмотрите переменные окружения сервиса
sudo systemctl show cloudtube | grep Environment
```

Должно быть:
```
Environment=PATH=... HOME=/home/cloudtube
```

## Автоматический скрипт исправления

Создайте и запустите скрипт:

```bash
cat > /tmp/fix_davfs2.sh << 'SCRIPT'
#!/bin/bash
set -e

echo "🔧 Исправление davfs2 для CloudTube"

# Получить пользователя сервиса
SERVICE_USER=$(grep "^User=" /etc/systemd/system/cloudtube.service | cut -d'=' -f2)
echo "Service user: $SERVICE_USER"

# Остановить сервис
echo "Stopping service..."
sudo systemctl stop cloudtube

# Создать домашнюю директорию
echo "Creating home directory..."
sudo mkdir -p "/home/$SERVICE_USER/.davfs2"
sudo chown -R $SERVICE_USER:$SERVICE_USER "/home/$SERVICE_USER"

# Создать конфигурацию
echo "Creating davfs2 config..."
sudo tee "/home/$SERVICE_USER/.davfs2/davfs2.conf" > /dev/null << 'EOF'
# davfs2 configuration
use_locks 0
cache_size 50
delay_upload 0
EOF
sudo chown $SERVICE_USER:$SERVICE_USER "/home/$SERVICE_USER/.davfs2/davfs2.conf"

# Обновить systemd сервис
echo "Updating systemd service..."
sudo sed -i 's/ProtectHome=true/ProtectHome=false/' /etc/systemd/system/cloudtube.service

# Добавить HOME если нет
if ! grep -q "Environment=\"HOME=" /etc/systemd/system/cloudtube.service; then
    sudo sed -i "/^Environment=\"PATH=/a Environment=\"HOME=/home/$SERVICE_USER\"" /etc/systemd/system/cloudtube.service
fi

# Добавить ReadWritePaths если нет
if ! grep -q "ReadWritePaths=.*\.davfs2" /etc/systemd/system/cloudtube.service; then
    sudo sed -i "s|ReadWritePaths=\(.*\)|ReadWritePaths=\1 /home/$SERVICE_USER/.davfs2 /mnt/yandex-disk|" /etc/systemd/system/cloudtube.service
fi

# Перезагрузить и запустить
echo "Reloading systemd..."
sudo systemctl daemon-reload
sudo systemctl start cloudtube

echo "✅ Done! Check status:"
sudo systemctl status cloudtube
SCRIPT

chmod +x /tmp/fix_davfs2.sh
sudo /tmp/fix_davfs2.sh
```

## Проверка после исправления

```bash
# 1. Статус сервиса
sudo systemctl status cloudtube

# 2. Логи (не должно быть ошибок Read-only file system)
sudo journalctl -u cloudtube -n 50

# 3. Файлы davfs2
SERVICE_USER=$(grep "^User=" /etc/systemd/system/cloudtube.service | cut -d'=' -f2)
sudo ls -la "/home/$SERVICE_USER/.davfs2/"

# 4. Попробуйте подключиться в Telegram
# /connect https://webdav.yandex.ru email@yandex.ru token
```

---

**Дата:** 2026-03-18  
**Версия:** 1.1  
**Автор:** Kir
