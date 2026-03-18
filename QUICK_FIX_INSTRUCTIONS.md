# 🚨 Быстрое исправление ошибки davfs2

## Проблема
```
Failed to setup davfs2: [Errno 30] Read-only file system: '/opt/CloudTube/.davfs2'
```

## ⚡ Быстрое решение (1 команда)

```bash
cd /opt/CloudTube
sudo bash fix_davfs2_permissions.sh
```

Скрипт автоматически:
1. ✅ Остановит бота
2. ✅ Создаст домашнюю директорию для пользователя
3. ✅ Настроит davfs2 конфигурацию
4. ✅ Обновит systemd сервис
5. ✅ Запустит бота

## Проверка

После выполнения скрипта:

1. **Проверьте статус:**
   ```bash
   sudo systemctl status cloudtube
   ```
   Должно быть: `active (running)`

2. **Проверьте логи:**
   ```bash
   sudo journalctl -u cloudtube -f
   ```
   Не должно быть ошибок "Read-only file system"

3. **Подключитесь в Telegram:**
   ```
   /connect https://webdav.yandex.ru ваш_email@yandex.ru ваш_oauth_токен
   ```

## Если нужен OAuth токен

```bash
cd /opt/CloudTube
source venv/bin/activate
python get_yandex_token.py
```

## Что было исправлено

### 1. Код (bot/webdav.py)
- Теперь использует правильную домашнюю директорию из переменной HOME
- Логирует путь к davfs2 для отладки

### 2. Systemd сервис
```ini
Environment="HOME=/home/cloudtube"  # Добавлено
ProtectHome=false                    # Было: true
ReadWritePaths=... /home/cloudtube/.davfs2 /mnt/yandex-disk  # Добавлено
```

### 3. Структура файлов
```
/home/cloudtube/
└── .davfs2/
    ├── davfs2.conf    # Конфигурация
    └── secrets        # Учетные данные (создается при /connect)
```

## Ручное исправление (если скрипт не работает)

### Шаг 1: Остановите бота
```bash
sudo systemctl stop cloudtube
```

### Шаг 2: Узнайте пользователя
```bash
SERVICE_USER=$(grep "^User=" /etc/systemd/system/cloudtube.service | cut -d'=' -f2)
echo $SERVICE_USER
```

### Шаг 3: Создайте директории
```bash
sudo mkdir -p "/home/$SERVICE_USER/.davfs2"
sudo chown -R $SERVICE_USER:$SERVICE_USER "/home/$SERVICE_USER"
```

### Шаг 4: Создайте конфигурацию
```bash
sudo tee "/home/$SERVICE_USER/.davfs2/davfs2.conf" > /dev/null << 'EOF'
use_locks 0
cache_size 50
delay_upload 0
EOF
```

### Шаг 5: Отредактируйте сервис
```bash
sudo nano /etc/systemd/system/cloudtube.service
```

Измените:
```ini
Environment="HOME=/home/cloudtube"  # Добавьте эту строку
ProtectHome=false                    # Измените с true на false
ReadWritePaths=/opt/CloudTube/data /opt/CloudTube/logs /opt/CloudTube/temp /home/cloudtube/.davfs2 /mnt/yandex-disk
```

### Шаг 6: Перезапустите
```bash
sudo systemctl daemon-reload
sudo systemctl start cloudtube
sudo systemctl status cloudtube
```

## Проверка работы

```bash
# 1. Файлы созданы?
SERVICE_USER=$(grep "^User=" /etc/systemd/system/cloudtube.service | cut -d'=' -f2)
sudo ls -la "/home/$SERVICE_USER/.davfs2/"

# 2. Сервис работает?
sudo systemctl status cloudtube

# 3. Нет ошибок в логах?
sudo journalctl -u cloudtube -n 50 | grep -i error

# 4. Попробуйте подключиться в Telegram
# /connect https://webdav.yandex.ru email token
```

## Дополнительная помощь

- 📖 Полная инструкция: [UPDATE_WEBDAV_FIX.md](UPDATE_WEBDAV_FIX.md)
- 🚀 Быстрый старт: [YANDEX_QUICKSTART.md](YANDEX_QUICKSTART.md)
- 🔧 Детальная настройка: [YANDEX_DISK_SETUP.md](YANDEX_DISK_SETUP.md)

---

**Дата:** 2026-03-18  
**Автор:** Kir
