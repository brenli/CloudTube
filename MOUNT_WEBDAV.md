# Монтирование Яндекс.Диска через WebDAV

## Преимущества
- ✅ Простое копирование файлов как в обычную папку
- ✅ Не нужен сложный код для загрузки
- ✅ Работает с любым токеном (OAuth или app password)
- ✅ Автоматическое переподключение при разрыве связи

## Установка

### 1. Установите davfs2

```bash
sudo apt update
sudo apt install davfs2
```

При установке выберите "Yes" когда спросят про непривилегированных пользователей.

### 2. Создайте точку монтирования

```bash
sudo mkdir -p /mnt/yandex-disk
sudo chown cld_test:cld_test /mnt/yandex-disk
```

### 3. Настройте учетные данные

Создайте файл с учетными данными:

```bash
mkdir -p ~/.davfs2
nano ~/.davfs2/secrets
```

Добавьте строку (замените на свои данные):

```
https://webdav.yandex.ru <ваш_email> <ваш_app_password>
```

Установите права доступа:

```bash
chmod 600 ~/.davfs2/secrets
```

### 4. Настройте davfs2

```bash
mkdir -p ~/.davfs2
cp /etc/davfs2/davfs2.conf ~/.davfs2/
nano ~/.davfs2/davfs2.conf
```

Раскомментируйте и измените:

```
use_locks 0
cache_size 50
```

### 5. Смонтируйте диск

```bash
mount.davfs https://webdav.yandex.ru /mnt/yandex-disk
```

Или добавьте в `/etc/fstab` для автомонтирования:

```bash
sudo nano /etc/fstab
```

Добавьте строку:

```
https://webdav.yandex.ru /mnt/yandex-disk davfs user,noauto,uid=cld_test,gid=cld_test 0 0
```

Теперь можно монтировать командой:

```bash
mount /mnt/yandex-disk
```

### 6. Проверьте монтирование

```bash
ls -la /mnt/yandex-disk
df -h /mnt/yandex-disk
```

## Использование в боте

Теперь вместо загрузки через WebDAV API просто копируйте файлы:

```python
import shutil

# Вместо await webdav_service.upload_file(local_path, remote_path)
# Просто копируем файл
shutil.copy(local_path, f"/mnt/yandex-disk/{remote_path}")
```

## Размонтирование

```bash
umount /mnt/yandex-disk
```

## Автомонтирование при загрузке

Добавьте в systemd service:

```bash
sudo nano /etc/systemd/system/cloudtube.service
```

Добавьте в секцию `[Service]`:

```
ExecStartPre=/bin/mount /mnt/yandex-disk
ExecStopPost=/bin/umount /mnt/yandex-disk
```

## Проблемы и решения

### Ошибка "Transport endpoint is not connected"

```bash
sudo umount -l /mnt/yandex-disk
mount /mnt/yandex-disk
```

### Медленная работа

Увеличьте кеш в `~/.davfs2/davfs2.conf`:

```
cache_size 100
```

### Проверка статуса

```bash
mount | grep yandex
```

## Важно

- WebDAV монтирование может быть медленным для больших файлов
- Используйте для небольших файлов или как временное решение
- Для production лучше использовать REST API с OAuth токеном
