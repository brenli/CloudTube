# 🚨 СРОЧНОЕ ИСПРАВЛЕНИЕ

## Проблема
Бот использует старую версию кода, которая пытается создать `.davfs2` в `/opt/CloudTube/` вместо домашней директории.

## ⚡ Быстрое решение (3 команды)

```bash
# 1. Остановить бота
sudo systemctl stop cloudtube

# 2. Обновить код
cd /opt/CloudTube && git pull

# 3. Применить исправления и запустить
sudo bash fix_davfs2_permissions.sh
```

## Если git pull не работает

Тогда вручную обнови файл `bot/webdav.py`:

```bash
# 1. Остановить бота
sudo systemctl stop cloudtube

# 2. Создать резервную копию
sudo cp /opt/CloudTube/bot/webdav.py /opt/CloudTube/bot/webdav.py.backup

# 3. Скачать обновленный файл
cd /opt/CloudTube
sudo wget -O bot/webdav.py https://raw.githubusercontent.com/brenli/CloudTube/main/bot/webdav.py

# 4. Применить исправления
sudo bash fix_davfs2_permissions.sh
```

## Или полностью вручную

### Шаг 1: Остановить бота
```bash
sudo systemctl stop cloudtube
```

### Шаг 2: Узнать пользователя сервиса
```bash
SERVICE_USER=$(grep "^User=" /etc/systemd/system/cloudtube.service | cut -d'=' -f2)
echo "Service user: $SERVICE_USER"
```

### Шаг 3: Создать домашнюю директорию
```bash
sudo mkdir -p "/home/$SERVICE_USER/.davfs2"
sudo chown -R $SERVICE_USER:$SERVICE_USER "/home/$SERVICE_USER"
```

### Шаг 4: Создать конфигурацию davfs2
```bash
sudo tee "/home/$SERVICE_USER/.davfs2/davfs2.conf" > /dev/null << 'EOF'
# davfs2 configuration
use_locks 0
cache_size 50
delay_upload 0
EOF

sudo chown $SERVICE_USER:$SERVICE_USER "/home/$SERVICE_USER/.davfs2/davfs2.conf"
```

### Шаг 5: Обновить systemd сервис
```bash
sudo nano /etc/systemd/system/cloudtube.service
```

Найди и измени эти строки:

**Было:**
```ini
ProtectHome=true
```

**Должно быть:**
```ini
Environment="HOME=/home/cloudtube"
ProtectHome=false
ReadWritePaths=/opt/CloudTube/data /opt/CloudTube/logs /opt/CloudTube/temp /home/cloudtube/.davfs2 /mnt/yandex-disk
```

Замени `cloudtube` на твоего пользователя!

### Шаг 6: Создать точку монтирования
```bash
sudo mkdir -p /mnt/yandex-disk
sudo chown $SERVICE_USER:$SERVICE_USER /mnt/yandex-disk
```

### Шаг 7: Перезапустить
```bash
sudo systemctl daemon-reload
sudo systemctl start cloudtube
```

### Шаг 8: Проверить
```bash
sudo systemctl status cloudtube
sudo journalctl -u cloudtube -f
```

## Проверка что исправление сработало

В логах должно быть:
```
Using davfs2 directory: /home/cloudtube/.davfs2
```

А НЕ:
```
Failed to setup davfs2: [Errno 30] Read-only file system: '/opt/CloudTube/.davfs2'
```

## После исправления

В Telegram выполни:
```
/connect https://webdav.yandex.ru ваш_email@yandex.ru ваш_oauth_токен
```

Должен ответить:
```
✅ Успешно подключено к Yandex.Disk
💾 Конфигурация сохранена
```

---

**ВАЖНО:** Проблема в том, что на сервере старая версия кода. Нужно обновить `bot/webdav.py` и systemd сервис!
