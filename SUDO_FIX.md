# Исправление проблемы с sudo и NoNewPrivileges

## Проблема
```
sudo: The "no new privileges" flag is set, which prevents sudo from running as root.
```

## Причина
`NoNewPrivileges=true` в systemd блокирует повышение привилегий внутри процесса, включая sudo.

## Решение
Дать пользователю `cloudtube` права на mount/umount через sudoers БЕЗ ПАРОЛЯ.

## Применение

```bash
sudo ./deploy_changes.sh
```

## Что изменено

### 1. Создан файл cloudtube-sudoers
Разрешает пользователю cloudtube:
- `mount -t davfs` в `/mnt/cloud_tube`
- `umount /mnt/cloud_tube`
- Создание и настройку mount point

### 2. Изменен bot/webdav.py
- Убраны попытки создать mount point из кода
- Добавлена проверка существования и прав
- Если mount point не существует - выдается понятная ошибка с инструкцией

### 3. Скрипт deploy_changes.sh
Автоматически:
- Устанавливает sudoers правила
- Проверяет синтаксис sudoers
- Создает все необходимые директории
- Обновляет код и конфигурацию

## Безопасность

Sudoers конфигурация разрешает ТОЛЬКО:
- Конкретные команды (mount, umount)
- Конкретную директорию (/mnt/cloud_tube)
- Конкретный тип файловой системы (davfs)

Это минимальные права, необходимые для работы.

## Альтернативные решения (не рекомендуется)

1. Убрать `NoNewPrivileges=true` из systemd
   - Снижает безопасность
   
2. Монтировать через systemd mount unit
   - Сложнее в настройке
   - Требует отдельного unit файла

3. Использовать fstab с опцией user
   - Требует хранения пароля в fstab или secrets
   - Менее гибко
