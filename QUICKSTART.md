# 🚀 Быстрый старт

## Windows

```powershell
# 1. Клонируйте репозиторий
git clone https://github.com/Kir-dev/CloudTube.git
cd CloudTube

# 2. Запустите установку
.\setup.bat

# 3. Отредактируйте .env (откроется автоматически)
# Заполните TELEGRAM_BOT_TOKEN и TELEGRAM_OWNER_ID

# 4. Запустите бота
.\venv\Scripts\Activate.ps1
python -m bot.main
```

## Linux/Mac

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/Kir-dev/CloudTube.git
cd CloudTube

# 2. Запустите установку
chmod +x setup.sh
./setup.sh

# 3. Отредактируйте .env
nano .env
# Заполните TELEGRAM_BOT_TOKEN и TELEGRAM_OWNER_ID

# 4. Запустите бота
source venv/bin/activate
python -m bot.main
```

## Получение токена бота

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте токен

## Получение вашего ID

1. Откройте [@userinfobot](https://t.me/userinfobot) в Telegram
2. Отправьте `/start`
3. Скопируйте ваш ID

## Первое использование

1. Найдите вашего бота в Telegram
2. Отправьте `/start`
3. Подключитесь к WebDAV: `/connect <url> <username> <password>`
4. Отправьте ссылку на YouTube видео
5. Выберите качество и настройки уведомлений
6. Готово! 🎉

## Подробная документация

- [INSTALLATION.md](INSTALLATION.md) - Полная инструкция по установке
- [WINDOWS_INSTALL.md](WINDOWS_INSTALL.md) - Установка на Windows
- [README.md](README.md) - Общая информация

## Нужна помощь?

- Проверьте [Issues](https://github.com/Kir-dev/CloudTube/issues)
- Создайте новый Issue
