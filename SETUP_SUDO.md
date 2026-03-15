# Настройка sudo для монтирования WebDAV

## 1. Создайте sudoers файл для пользователя

```bash
sudo visudo -f /etc/sudoers.d/cloudtube
```

## 2. Добавьте следующие строки (замените cld_test на вашего пользователя):

```
cld_test ALL=(ALL) NOPASSWD: /bin/mkdir -p /mnt/yandex-disk
cld_test ALL=(ALL) NOPASSWD: /sbin/mount.davfs * /mnt/yandex-disk
cld_test ALL=(ALL) NOPASSWD: /bin/mount.davfs * /mnt/yandex-disk
cld_test ALL=(ALL) NOPASSWD: /bin/umount /mnt/yandex-disk
cld_test ALL=(ALL) NOPASSWD: /bin/umount -l /mnt/yandex-disk
```

## 3. Сохраните и выйдите (Ctrl+X, Y, Enter)

## 4. Проверьте права:

```bash
sudo -l
```

Должно показать команды без запроса пароля.

## 5. Перезапустите бот:

```bash
sudo systemctl restart cloudtube
```

## 6. Попробуйте подключиться:

```
/connect https://webdav.yandex.ru <email> <токен>
```
