# Применение изменений

## Что изменено

1. ✅ Точка монтирования: `/mnt/yandex-disk` → `/mnt/cloud_tube`
2. ✅ Конфигурация davfs2: `/home/cloudtube/.davfs2`
3. ✅ Автоматическая проверка и установка прав на mount point
4. ✅ Обновлена systemd конфигурация
5. ✅ Обновлен скрипт установки

## Команды для применения

```bash
# Шаг 1: Сделать скрипт исполняемым
chmod +x fix_cloudtube_home.sh

# Шаг 2: Запустить скрипт (создаст все директории и установит права)
sudo ./fix_cloudtube_home.sh
```

## Что делает скрипт

1. Создает `/home/cloudtube` с правами `cloudtube:cloudtube`
2. Создает `/home/cloudtube/.davfs2` с правами `700`
3. Создает `/mnt/cloud_tube` с правами `cloudtube:cloudtube`
4. Перезагружает systemd конфигурацию
5. Перезапускает сервис cloudtube
6. Показывает статус сервиса

## Проверка результата

```bash
# Смотрим логи в реальном времени
sudo journalctl -u cloudtube -f
```

Должны увидеть:
```
Using davfs2 directory: /home/cloudtube/.davfs2
Creating mount point /mnt/cloud_tube
Mount point already owned by cloudtube
Mounting WebDAV...
```

## Если что-то пошло не так

```bash
# Проверить права на директории
ls -ld /home/cloudtube
ls -ld /home/cloudtube/.davfs2
ls -ld /mnt/cloud_tube

# Проверить статус сервиса
sudo systemctl status cloudtube

# Посмотреть последние ошибки
sudo journalctl -u cloudtube -n 50 --no-pager
```
