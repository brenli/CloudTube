# Исправление ошибки davfs2: Read-only file system

## Проблема
```
OSError: [Errno 30] Read-only file system: '/opt/CloudTube/.davfs2'
```

Сервис пытался создать директорию `.davfs2` в `/opt/CloudTube/`, которая является read-only или принадлежит root.

## Причина
Код использовал переменные окружения `HOME`, `USER`, `USERNAME` для определения домашней директории пользователя. При запуске через systemd эти переменные могут быть не установлены или указывать на неправильные пути.

## Решение
Заменил определение домашней директории на использование модуля `pwd`:

```python
import pwd

uid = os.getuid()
user_info = pwd.getpwuid(uid)
home_dir = user_info.pw_dir
username = user_info.pw_name
```

## Изменения в bot/webdav.py

1. Добавлен импорт `pwd` в начало файла
2. Метод `_setup_davfs2()`: использует `pwd.getpwuid(os.getuid())` вместо переменных окружения
3. Метод `connect()`: использует `pwd.getpwuid(os.getuid())` для определения владельца mount point
4. Метод `_mount_webdav()`: использует `pwd.getpwuid(os.getuid())` для получения uid/gid

## Результат
Теперь код корректно определяет домашнюю директорию пользователя, под которым запущен процесс, независимо от переменных окружения. Директория `.davfs2` будет создана в правильном месте (например, `/root/.davfs2` или `/home/username/.davfs2`).
