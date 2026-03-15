# Полное решение проблемы медленной загрузки

## Диагностика

Проблема: В базе данных сохранен обычный пароль "cyob..." вместо OAuth токена.

Лог показывает:
```
OAuth mode: False, Password prefix: cyob
Using WebDAV PUT for upload (Basic Auth)
```

Это приводит к использованию WebDAV PUT, который Яндекс.Диск throttling до 60 секунд на мегабайт (2 часа для 114MB файла).

## Решение

### Шаг 1: Остановить текущую загрузку

```bash
sudo systemctl stop cloudtube
sudo pkill -9 -f cloudtube
rm -f /opt/CloudTube/temp/download_*.mp4
rm -f /opt/CloudTube/temp/download_*.m4a
```

### Шаг 2: Проверить токен в БД (опционально)

```bash
cd /opt/CloudTube
source venv/bin/activate
python check_db_token.py
```

### Шаг 3: Запустить бот

```bash
sudo systemctl start cloudtube
```

### Шаг 4: Переподключиться с OAuth токеном

В Telegram отправьте команду:

```
/connect https://webdav.yandex.ru <ваш_email> <oauth_token>
```

**ВАЖНО:** OAuth токен должен начинаться с одного из префиксов:
- `y0_` (новый формат)
- `t1.` (старый формат)
- `AQAA` (альтернативный формат)

Если у вас нет OAuth токена, получите его:

```bash
cd /opt/CloudTube
source venv/bin/activate
python get_yandex_token.py
```

### Шаг 5: Проверить подключение

```
/settings
```

Должно показать:
```
✅ WebDAV: Подключено
💾 Место: X.XX GB свободно из X.XX GB
```

### Шаг 6: Загрузить видео

Отправьте ссылку на видео. В логах должно быть:

```
OAuth mode: True, Password prefix: y0_X (или t1.X или AQAAX)
Using REST API for upload (OAuth detected)
Got REST API upload URL, starting streaming PUT
REST API upload response: 201
Upload completed successfully via REST API
```

Загрузка 114MB файла займет 10-30 секунд вместо 2 часов.

## Что было исправлено в коде

1. ✅ Добавлена автоматическая загрузка WebDAV конфигурации из БД при старте
2. ✅ Добавлено сохранение конфигурации в БД при `/connect`
3. ✅ Добавлены логи для диагностики OAuth режима
4. ✅ Гибридный подход: REST API для OAuth, WebDAV для Basic Auth
5. ✅ Автоматическое определение типа токена по префиксу

## Проверка работы

После переподключения с OAuth токеном:

```bash
sudo journalctl -u cloudtube -f
```

Отправьте короткое видео для теста. В логах должно быть:
- `OAuth mode: True`
- `Using REST API for upload`
- `Upload completed successfully via REST API`

Время загрузки: ~10-30 секунд для файлов 100-200MB.
