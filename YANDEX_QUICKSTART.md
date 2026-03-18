# Быстрый старт с Яндекс.Диском

Это краткое руководство поможет вам быстро настроить CloudTube для работы с Яндекс.Диском.

## За 5 минут до первой загрузки

### 1. Установка (Ubuntu/Debian)

```bash
# Клонируйте репозиторий
git clone https://github.com/brenli/CloudTube.git
cd CloudTube

# Запустите автоматическую установку
chmod +x install.sh
./install.sh
```

Скрипт автоматически установит:
- Python 3.11
- FFmpeg
- davfs2
- Все необходимые зависимости

### 2. Получение OAuth токена

```bash
# Запустите скрипт получения токена
python get_yandex_token.py
```

Скрипт:
1. Откроет браузер с формой авторизации Яндекс
2. Попросит разрешить доступ к Яндекс.Диску
3. Автоматически получит и сохранит OAuth токен

**Альтернатива:** Получите токен вручную на https://oauth.yandex.ru/authorize?response_type=token&client_id=23cabbbdc6cd418abb4b39c32c41195d

### 3. Настройка бота

```bash
# Отредактируйте конфигурацию
nano .env
```

Заполните только 2 параметра:
```bash
TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather
TELEGRAM_OWNER_ID=ваш_telegram_id
```

**Как получить:**
- Токен бота: напишите [@BotFather](https://t.me/BotFather) в Telegram
- Ваш ID: напишите [@userinfobot](https://t.me/userinfobot) в Telegram

### 4. Запуск бота

```bash
# Активируйте виртуальное окружение
source venv/bin/activate

# Запустите бота
python -m bot.main
```

### 5. Подключение Яндекс.Диска

Откройте Telegram и напишите боту:

```
/connect https://webdav.yandex.ru ваш_email@yandex.ru ваш_oauth_токен
```

Пример:
```
/connect https://webdav.yandex.ru ivan@yandex.ru y0_AgAAAAABCDEFGHIJKLMNOPQRSTUVWXYZ
```

Бот ответит: ✅ Успешно подключено к Yandex.Disk

### 6. Первая загрузка

Отправьте боту ссылку на любое видео YouTube:
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

Выберите качество и настройки уведомлений. Готово! 🎉

## Проверка работы

### Тест монтирования

```bash
# Запустите тестовый скрипт
chmod +x test_yandex_mount.sh
./test_yandex_mount.sh
```

Скрипт проверит:
- ✅ Установлен ли davfs2
- ✅ Корректны ли учетные данные
- ✅ Работает ли монтирование
- ✅ Доступна ли запись на диск

### Проверка статуса в боте

```
/status
```

Должно показать:
```
📊 Статус системы

✅ WebDAV: Подключено
💾 Место: XX.XX GB свободно из XX.XX GB
📥 Нет активных загрузок
```

## Структура файлов

После загрузки видео будут организованы так:

```
Яндекс.Диск/
├── Single Videos/          # Отдельные видео
│   └── Rick Astley - Never Gonna Give You Up.mp4
└── My Playlist/            # Плейлисты
    ├── Video 1.mp4
    ├── Video 2.mp4
    └── Video 3.mp4
```

## Автозапуск (опционально)

Чтобы бот запускался автоматически при загрузке системы:

```bash
# Установите как системный сервис
sudo systemctl enable cloudtube
sudo systemctl start cloudtube

# Проверьте статус
sudo systemctl status cloudtube

# Просмотр логов
sudo journalctl -u cloudtube -f
```

## Полезные команды

```bash
# Просмотр логов бота
tail -f logs/bot.log

# Обновление yt-dlp (если YouTube блокирует)
./update_ytdlp.sh

# Перезапуск бота
sudo systemctl restart cloudtube

# Остановка бота
sudo systemctl stop cloudtube
```

## Команды бота

- `/start` - Приветствие и список команд
- `/help` - Подробная справка
- `/status` - Статус системы и активные загрузки
- `/history` - История всех загрузок
- `/cancel <task_id>` - Отменить загрузку
- `/pause <task_id>` - Приостановить загрузку
- `/resume <task_id>` - Возобновить загрузку

## Что дальше?

- 📖 Полная документация: [README.md](README.md)
- 🔧 Детальная настройка Яндекс.Диска: [YANDEX_DISK_SETUP.md](YANDEX_DISK_SETUP.md)
- 🐛 Проблемы? См. раздел FAQ в [README.md](README.md)

## Частые вопросы

**Q: Сколько действует OAuth токен?**  
A: 1 год. После истечения получите новый через `python get_yandex_token.py`

**Q: Можно ли загружать плейлисты?**  
A: Да! Просто отправьте ссылку на плейлист. Бот создаст отдельную папку.

**Q: Сколько видео можно загружать одновременно?**  
A: По умолчанию 2. Настраивается в `.env` параметром `MAX_CONCURRENT_DOWNLOADS`

**Q: Что делать если YouTube блокирует загрузку?**  
A: Обновите yt-dlp: `./update_ytdlp.sh` и перезапустите бота

**Q: Как посмотреть загруженные видео?**  
A: Откройте https://disk.yandex.ru в браузере или используйте мобильное приложение

---

🎉 **Готово!** Теперь вы можете загружать видео с YouTube прямо на Яндекс.Диск через Telegram!

Если что-то не работает, см. [YANDEX_DISK_SETUP.md](YANDEX_DISK_SETUP.md) для детальной диагностики.
