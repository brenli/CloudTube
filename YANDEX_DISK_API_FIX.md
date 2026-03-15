# Решение проблемы с Yandex.Disk WebDAV

## Проблема

Yandex.Disk вводит искусственную задержку **60 секунд на каждый мегабайт** при использовании WebDAV протокола. Это делает невозможным загрузку файлов больше нескольких мегабайт из-за socket timeout.

Источники:
- [Zotero Forums](https://forums.zotero.org/discussion/106004/webdav-on-yandex-is-slow): "For every megabyte of data uploaded or downloaded, Yandex Disk introduces a 60-second delay"
- [DevonThink Forums](https://discourse.devontechnologies.com/t/sync-with-slow-webdav-could-we-just-wait-instead-of-timeout/60862): "inject artificial timeouts adding 60sec delay per MB"

## Решение

Использовать **Yandex.Disk REST API** вместо WebDAV. REST API не имеет таких ограничений.

## Изменения

### 1. Зависимости (requirements.txt)

Заменили:
```
webdav4==0.9.8
```

На:
```
yadisk[async_files]==3.1.0
```

### 2. Код (bot/webdav.py)

- Заменили `webdav4.Client` на `yadisk.AsyncClient`
- Убрали все WebDAV-специфичные вызовы (PROPFIND, MKCOL, etc.)
- Используем REST API методы: `upload()`, `mkdir()`, `exists()`, `get_disk_info()`

### 3. Конфигурация

**ВАЖНО**: Теперь вместо пароля нужен OAuth токен!

#### Как получить OAuth токен:

1. Перейдите на https://oauth.yandex.ru/
2. Зарегистрируйте новое приложение
3. Получите OAuth токен с правами на Yandex.Disk
4. Используйте этот токен вместо пароля в настройках бота

#### Или используйте простой способ:

```python
import yadisk

# Получить токен через код подтверждения
client = yadisk.Client(id="<app-id>", secret="<app-secret>")
url = client.get_code_url()
print(f"Перейдите по ссылке: {url}")
code = input("Введите код: ")
response = client.get_token(code)
print(f"Ваш токен: {response.access_token}")
```

## Применение

```bash
# 1. Установите новую зависимость
cd /opt/CloudTube
source venv/bin/activate
pip install 'yadisk[async_files]==3.1.0'

# 2. Получите OAuth токен (см. выше)

# 3. Обновите конфигурацию бота
# В .env или через /settings в боте:
# WEBDAV_PASSWORD=<ваш-oauth-токен>

# 4. Перезапустите бота
sudo systemctl restart cloudtube

# 5. Проверьте логи
sudo journalctl -u cloudtube -f
```

## Преимущества

1. ✅ Нет искусственных задержек
2. ✅ Быстрая загрузка файлов любого размера
3. ✅ Нативная поддержка асинхронности
4. ✅ Более надежное API
5. ✅ Лучшая обработка ошибок

## Ожидаемые логи

```
INFO - Uploading file: ... (120247586 bytes / 114.7 MB) to /Single Videos/video.mp4
INFO - Creating directory: /Single Videos
INFO - Starting upload to: /Single Videos/video.mp4
INFO - Upload completed successfully
```

Загрузка 114 MB файла займет ~10-30 секунд вместо 114 минут с WebDAV!
