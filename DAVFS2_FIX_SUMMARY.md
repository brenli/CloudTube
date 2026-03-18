# Исправление ошибки davfs2: Read-only file system

## Проблема
```
OSError: [Errno 30] Read-only file system: '/opt/CloudTube/.davfs2'
```

Сервис пытался создать директорию `.davfs2` в `/opt/CloudTube/`, которая защищена `ProtectSystem=strict` в systemd.

## Причина
1. Пользователь `cloudtube` был создан с домашней директорией `/opt/CloudTube` в `/etc/passwd`
2. Systemd устанавливает `HOME=/home/cloudtube` в переменных окружения
3. Но `pwd.getpwuid()` возвращает `/opt/CloudTube` из базы данных пользователей
4. `ProtectSystem=strict` делает `/opt/CloudTube` read-only для безопасности

## Решение

### 1. Исправлен код в bot/webdav.py
Теперь приоритет отдается переменной окружения `HOME` (установленной systemd), а не базе данных `pwd`:

```python
# Prefer HOME env var (set by systemd) over pwd database
home_dir = os.environ.get('HOME')

if not home_dir:
    # Fallback to pwd if HOME not set
    uid = os.getuid()
    user_info = pwd.getpwuid(uid)
    home_dir = user_info.pw_dir
```

### 2. Создан скрипт fix_cloudtube_home.sh
Скрипт создает и настраивает `/home/cloudtube`:

```bash
chmod +x fix_cloudtube_home.sh
sudo ./fix_cloudtube_home.sh
```

Скрипт:
- Создает `/home/cloudtube` если не существует
- Устанавливает правильные права доступа
- Создает `/home/cloudtube/.davfs2`
- Перезапускает сервис

### 3. Systemd конфигурация
В `systemd/cloudtube.service` уже настроено:
- `Environment="HOME=/home/cloudtube"` - устанавливает HOME
- `ReadWritePaths=/home/cloudtube/.davfs2` - разрешает запись в .davfs2

## Результат
Теперь `.davfs2` создается в `/home/cloudtube/.davfs2`, который доступен для записи и разрешен в systemd конфигурации.
