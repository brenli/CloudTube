# Исправление токена

## Проблема
В БД сохранен старый пароль "cyob..." вместо OAuth токена.

## Решение

1. Остановите бот:
```bash
sudo systemctl stop cloudtube
sudo pkill -9 -f cloudtube
```

2. Очистите временные файлы:
```bash
rm -f /opt/CloudTube/temp/download_*.mp4
rm -f /opt/CloudTube/temp/download_*.m4a
```

3. Запустите бот:
```bash
sudo systemctl start cloudtube
```

4. В Telegram отправьте команду `/connect` с ПРАВИЛЬНЫМ OAuth токеном:
```
/connect https://webdav.yandex.ru <email> <ваш_oauth_token>
```

OAuth токен должен начинаться с `y0_` или `t1.` или `AQAA`

5. Проверьте подключение:
```
/settings
```

6. Попробуйте загрузить видео снова.
