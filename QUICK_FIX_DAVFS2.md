# Быстрое исправление ошибки davfs2

## Проблема
```
OSError: [Errno 30] Read-only file system: '/opt/CloudTube/.davfs2'
```

## Решение (выполните эти команды)

```bash
# 1. Сделать скрипт исполняемым
chmod +x fix_cloudtube_home.sh

# 2. Запустить скрипт исправления
sudo ./fix_cloudtube_home.sh
```

Скрипт автоматически:
- Создаст `/home/cloudtube` если не существует
- Установит правильные права доступа
- Создаст `/home/cloudtube/.davfs2`
- Создаст точку монтирования `/mnt/cloud_tube`
- Установит права на `/mnt/cloud_tube`
- Перезагрузит systemd конфигурацию
- Перезапустит сервис

## Проверка

После выполнения скрипта проверьте логи:

```bash
sudo journalctl -u cloudtube -f
```

Вы должны увидеть:
```
Using davfs2 directory: /home/cloudtube/.davfs2
Creating mount point /mnt/cloud_tube
```

## Что было изменено

1. **Точка монтирования**: `/mnt/yandex-disk` → `/mnt/cloud_tube`
2. **Конфигурация davfs2**: использует `/home/cloudtube/.davfs2`
3. **Проверка прав**: автоматическая проверка и установка прав на mount point
4. **Systemd**: обновлен `ReadWritePaths` для `/mnt/cloud_tube`

## Структура директорий

```
/home/cloudtube/
  └── .davfs2/          # конфигурация davfs2
      ├── secrets       # учетные данные
      └── davfs2.conf   # настройки

/mnt/cloud_tube/        # точка монтирования Яндекс.Диска
```
