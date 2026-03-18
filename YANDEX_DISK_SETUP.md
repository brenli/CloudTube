# Настройка Яндекс.Диска для CloudTube

Это руководство поможет вам настроить автоматическую загрузку видео на Яндекс.Диск через WebDAV.

## Требования

- Ubuntu 22.04/24.04 (или другой Linux с davfs2)
- Аккаунт Яндекс.Диска
- Установленный davfs2

## Шаг 1: Установка davfs2

```bash
sudo apt update
sudo apt install davfs2
```

При установке вас спросят, разрешить ли непривилегированным пользователям монтировать WebDAV. Выберите **Да**.

## Шаг 2: Получение OAuth токена

Яндекс.Диск требует OAuth токен для доступа через WebDAV API.

### Автоматический способ (рекомендуется):

```bash
python get_yandex_token.py
```

Скрипт откроет браузер для авторизации и автоматически получит токен.

### Ручной способ:

1. Перейдите на https://oauth.yandex.ru/authorize?response_type=token&client_id=23cabbbdc6cd418abb4b39c32c41195d
2. Разрешите доступ к Яндекс.Диску
3. Скопируйте токен из адресной строки (после `access_token=`)

## Шаг 3: Настройка davfs2

### Создание конфигурации пользователя:

```bash
mkdir -p ~/.davfs2
```

### Создание файла конфигурации:

```bash
cat > ~/.davfs2/davfs2.conf << 'EOF'
# davfs2 configuration
use_locks 0
cache_size 50
delay_upload 0
EOF
```

### Создание файла с учетными данными:

```bash
cat > ~/.davfs2/secrets << 'EOF'
https://webdav.yandex.ru ваш_email@yandex.ru ваш_oauth_токен
EOF

chmod 600 ~/.davfs2/secrets
```

**Важно:** Замените `ваш_email@yandex.ru` и `ваш_oauth_токен` на ваши данные!

## Шаг 4: Создание точки монтирования

```bash
sudo mkdir -p /mnt/yandex-disk
sudo chown $USER:$USER /mnt/yandex-disk
```

## Шаг 5: Настройка sudo для монтирования без пароля (опционально)

Чтобы бот мог монтировать диск автоматически:

```bash
sudo visudo
```

Добавьте в конец файла (замените `username` на ваше имя пользователя):

```
username ALL=(ALL) NOPASSWD: /bin/mount -t davfs https\://webdav.yandex.ru /mnt/yandex-disk *
username ALL=(ALL) NOPASSWD: /bin/umount /mnt/yandex-disk
username ALL=(ALL) NOPASSWD: /bin/mkdir -p /mnt/yandex-disk
```

## Шаг 6: Тестирование монтирования

Проверьте, что диск монтируется корректно:

```bash
sudo mount -t davfs https://webdav.yandex.ru /mnt/yandex-disk -o uid=$UID,gid=$GID
```

Если монтирование прошло успешно, проверьте доступ:

```bash
ls -la /mnt/yandex-disk
```

Размонтируйте:

```bash
sudo umount /mnt/yandex-disk
```

## Шаг 7: Подключение в боте

Запустите бота и используйте команду:

```
/connect https://webdav.yandex.ru ваш_email@yandex.ru ваш_oauth_токен
```

Бот автоматически:
1. Сохранит учетные данные в `~/.davfs2/secrets`
2. Примонтирует Яндекс.Диск к `/mnt/yandex-disk`
3. Начнет загружать видео на диск

## Структура файлов на Яндекс.Диске

Бот организует файлы следующим образом:

```
/
├── Single Videos/          # Отдельные видео
│   ├── video1.mp4
│   └── video2.mp4
└── Playlist Name/          # Плейлисты
    ├── video1.mp4
    ├── video2.mp4
    └── video3.mp4
```

## Проверка статуса

Используйте команду `/status` в боте для проверки:
- Статуса подключения к Яндекс.Диску
- Доступного места
- Активных загрузок

## Устранение проблем

### Ошибка: "mount.davfs: mounting failed"

1. Проверьте OAuth токен (он действителен 1 год)
2. Убедитесь, что файл `~/.davfs2/secrets` имеет права 600
3. Проверьте, что davfs2 установлен: `which mount.davfs`

### Ошибка: "Permission denied"

1. Убедитесь, что точка монтирования принадлежит вашему пользователю:
   ```bash
   sudo chown $USER:$USER /mnt/yandex-disk
   ```

2. Проверьте настройки sudo (Шаг 5)

### Диск не монтируется автоматически

1. Проверьте логи бота: `tail -f logs/bot.log`
2. Попробуйте монтирование вручную (Шаг 6)
3. Убедитесь, что учетные данные в `~/.davfs2/secrets` корректны

### Медленная загрузка

1. Увеличьте `cache_size` в `~/.davfs2/davfs2.conf`
2. Проверьте скорость интернет-соединения
3. Используйте более низкое качество видео

## Безопасность

- OAuth токен хранится в `~/.davfs2/secrets` с правами 600 (только владелец может читать)
- Токен также сохраняется в базе данных бота (SQLite)
- Рекомендуется использовать отдельный аккаунт Яндекс для бота
- Регулярно обновляйте OAuth токен (срок действия 1 год)

## Дополнительная информация

- [Документация Яндекс.Диска WebDAV](https://yandex.ru/dev/disk/api/concepts/about.html)
- [Документация davfs2](https://savannah.nongnu.org/projects/davfs2)
- [OAuth токены Яндекс](https://yandex.ru/dev/oauth/)
