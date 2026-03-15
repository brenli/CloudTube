# Установка обновленной версии с yadisk

## Что изменилось

Заменил самописный код WebDAV на официальную библиотеку `yadisk` от Яндекса.

**Преимущества:**
- ✅ Быстрая загрузка через REST API (10-30 секунд вместо 2 часов)
- ✅ Надежная работа с Яндекс.Диском
- ✅ Автоматическое создание папок
- ✅ Поддержка async/await
- ✅ Официальная поддержка от Яндекса

## Установка

### 1. Остановите бот

```bash
sudo systemctl stop cloudtube
sudo pkill -9 -f cloudtube
```

### 2. Очистите временные файлы

```bash
cd /opt/CloudTube
rm -f temp/download_*.mp4
rm -f temp/download_*.m4a
```

### 3. Обновите зависимости

```bash
source venv/bin/activate
pip install --upgrade 'yadisk[async_files]==3.4.0'
```

### 4. Получите OAuth токен

```bash
python get_yandex_token.py
```

Следуйте инструкциям. Токен будет начинаться с `y0_`, `y1_`, `y2_` или `y3_`.

### 5. Запустите бот

```bash
sudo systemctl start cloudtube
sudo journalctl -u cloudtube -f
```

### 6. Подключитесь с OAuth токеном

В Telegram отправьте:

```
/connect https://webdav.yandex.ru <ваш_email> <y0_токен>
```

Должно появиться:
```
✅ Успешно подключено к Yandex.Disk
💾 Конфигурация сохранена
🚀 Загрузка будет быстрой через REST API
```

### 7. Проверьте подключение

```
/settings
```

### 8. Загрузите тестовое видео

Отправьте короткую ссылку на YouTube. Загрузка должна занять 10-30 секунд.

## Логи

В логах должно быть:

```
Connected to Yandex.Disk successfully
Uploading ./temp/download_xxx.mp4 (114.7 MB) → Single Videos/download_xxx.mp4
Upload completed successfully
```

## Важно

- ❌ App password больше НЕ поддерживается
- ✅ Только OAuth токены (y0_, y1_, y2_, y3_)
- ✅ Токен получается через `get_yandex_token.py`
- ✅ Загрузка всегда быстрая через REST API

## Если что-то не работает

1. Проверьте что токен начинается с `y0_`, `y1_`, `y2_` или `y3_`
2. Проверьте что токен не истек (срок действия 1 год)
3. Проверьте логи: `sudo journalctl -u cloudtube -f`
4. Переподключитесь: `/connect https://webdav.yandex.ru <email> <токен>`
