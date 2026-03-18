# Изменения точки монтирования и проверки прав

## Изменения

### 1. Новая точка монтирования
- **Было**: `/mnt/yandex-disk`
- **Стало**: `/mnt/cloud_tube`

### 2. Автоматическая проверка и установка прав

Метод `connect()` теперь:

1. **Создает mount point** если не существует
   ```python
   sudo mkdir -p /mnt/cloud_tube
   ```

2. **Проверяет владельца** через `os.stat()`
   - Сравнивает текущий UID/GID с UID/GID процесса
   - Если не совпадают - устанавливает правильного владельца

3. **Проверяет права на запись** через `os.access()`
   - Если нет прав на запись - устанавливает `chmod 755`

4. **Логирует все действия** для отладки

### 3. Обновлена systemd конфигурация

В `systemd/cloudtube.service`:
```ini
ReadWritePaths=/opt/CloudTube/data /opt/CloudTube/logs /opt/CloudTube/temp /home/cloudtube/.davfs2 /mnt/cloud_tube
```

### 4. Обновлен скрипт установки

`fix_cloudtube_home.sh` теперь:
- Создает `/home/cloudtube/.davfs2`
- Создает `/mnt/cloud_tube`
- Устанавливает права на оба каталога
- Перезагружает systemd конфигурацию

## Применение изменений

```bash
# 1. Сделать скрипт исполняемым
chmod +x fix_cloudtube_home.sh

# 2. Запустить скрипт
sudo ./fix_cloudtube_home.sh
```

## Проверка

```bash
# Проверить права на mount point
ls -ld /mnt/cloud_tube

# Должно быть:
# drwxr-xr-x 2 cloudtube cloudtube 4096 ... /mnt/cloud_tube

# Проверить логи
sudo journalctl -u cloudtube -f
```

## Логика работы

```
1. Сервис запускается под пользователем cloudtube
2. Код получает UID/GID процесса (cloudtube)
3. Проверяет существование /mnt/cloud_tube
4. Если нет - создает с sudo
5. Проверяет владельца директории
6. Если владелец не cloudtube - меняет владельца
7. Проверяет права на запись
8. Если нет прав - устанавливает chmod 755
9. Монтирует Яндекс.Диск в /mnt/cloud_tube
10. Загруженные файлы копируются в /mnt/cloud_tube
```

## Безопасность

- `ProtectSystem=strict` - защищает системные директории
- `/mnt/cloud_tube` добавлен в `ReadWritePaths` - разрешена запись
- Владелец `cloudtube:cloudtube` - только этот пользователь может писать
- Права `755` - другие могут читать, но не писать
