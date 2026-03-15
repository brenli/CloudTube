# Применение исправления Yandex.Disk API

## Проблема
WebDAV на Yandex.Disk имеет искусственную задержку 60 секунд на каждый мегабайт. Это делает невозможным загрузку файлов.

## Решение
Использовать Yandex.Disk REST API вместо WebDAV.

## Шаги

### 1. Установите новую библиотеку

```bash
cd /opt/CloudTube
source venv/bin/activate
pip install 'yadisk[async_files]==3.1.0'
```

### 2. Получите OAuth токен

#### Вариант A: Через скрипт (рекомендуется)

```bash
python3 get_yandex_token.py
```

Следуйте инструкциям на экране.

#### Вариант B: Вручную

1. Перейдите на https://oauth.yandex.ru/
2. Нажмите "Зарегистрировать новое приложение"
3. Заполните форму:
   - Название: CloudTube Bot
   - Платформы: Web-сервисы
   - Redirect URI: https://oauth.yandex.ru/verification_code
   - Права: Яндекс.Диск REST API (cloud_api:disk.write)
4. Скопируйте Client ID и Client Secret
5. Используйте скрипт `get_yandex_token.py` с этими данными

### 3. Обновите конфигурацию

Откройте файл `.env` и замените:

```bash
WEBDAV_URL=https://webdav.yandex.ru
WEBDAV_USERNAME=ваш_логин
WEBDAV_PASSWORD=ваш_пароль
```

На:

```bash
WEBDAV_URL=https://cloud-api.yandex.net/v1/disk
WEBDAV_USERNAME=не_используется
WEBDAV_PASSWORD=ваш_oauth_токен_из_шага_2
```

**ВАЖНО**: В поле `WEBDAV_PASSWORD` теперь должен быть OAuth токен, а не пароль!

### 4. Перезапустите бота

```bash
sudo systemctl restart cloudtube
sudo journalctl -u cloudtube -f
```

### 5. Проверьте работу

Отправьте боту тестовое видео. В логах должно быть:

```
INFO - Uploading file: ... to /Single Videos/video.mp4
INFO - Starting upload to: /Single Videos/video.mp4
INFO - Upload completed successfully
```

Файл должен появиться в Yandex.Disk в папке "Single Videos".

## Проверка токена

Если хотите проверить что токен работает:

```python
import yadisk

client = yadisk.Client(token="ваш_токен")
print(client.check_token())  # Должно вывести True
print(client.get_disk_info())  # Должно показать информацию о диске
```

## Troubleshooting

### Ошибка "Token invalid"

- Проверьте что токен скопирован полностью
- Убедитесь что при создании приложения выбрали права на Yandex.Disk
- Попробуйте получить новый токен

### Ошибка "Not connected to Yandex.Disk"

- Проверьте что в `.env` указан правильный токен
- Перезапустите бота после изменения `.env`

### Файлы не загружаются

- Проверьте логи: `sudo journalctl -u cloudtube -n 100`
- Убедитесь что токен валиден
- Проверьте что на Yandex.Disk есть свободное место

## Преимущества

- ✅ Загрузка 100 MB файла: ~10-30 секунд (вместо 100 минут с WebDAV)
- ✅ Нет искусственных задержек
- ✅ Более надежное API
- ✅ Поддержка файлов любого размера
