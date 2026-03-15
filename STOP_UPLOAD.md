# Остановка застрявшей загрузки

Выполните команды:

```bash
# Остановить бот
sudo systemctl stop cloudtube

# Проверить что процесс остановлен
ps aux | grep python

# Если процесс еще работает, убить его
sudo pkill -9 -f cloudtube

# Очистить временные файлы
rm -f /opt/CloudTube/temp/download_*.mp4
rm -f /opt/CloudTube/temp/download_*.m4a

# Перезапустить бот
sudo systemctl start cloudtube
sudo journalctl -u cloudtube -f
```

После этого отправьте `/settings` в бот чтобы проверить подключение.
