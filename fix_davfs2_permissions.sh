#!/bin/bash
# Quick fix script for davfs2 permissions issue
# Run with: sudo bash fix_davfs2_permissions.sh

set -e

echo "🔧 CloudTube - Исправление davfs2"
echo "=================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Запустите скрипт с sudo:"
    echo "   sudo bash fix_davfs2_permissions.sh"
    exit 1
fi

# Get service user
if [ ! -f /etc/systemd/system/cloudtube.service ]; then
    echo "❌ Файл сервиса не найден: /etc/systemd/system/cloudtube.service"
    echo "   Установите CloudTube сначала"
    exit 1
fi

SERVICE_USER=$(grep "^User=" /etc/systemd/system/cloudtube.service | cut -d'=' -f2)
echo "📋 Пользователь сервиса: $SERVICE_USER"
echo ""

# Stop service
echo "⏸️  Остановка сервиса..."
systemctl stop cloudtube
echo "✅ Сервис остановлен"
echo ""

# Create home directory
echo "📁 Создание домашней директории..."
mkdir -p "/home/$SERVICE_USER/.davfs2"
chown -R $SERVICE_USER:$SERVICE_USER "/home/$SERVICE_USER"
echo "✅ Домашняя директория создана: /home/$SERVICE_USER"
echo ""

# Create davfs2 config
echo "⚙️  Создание конфигурации davfs2..."
cat > "/home/$SERVICE_USER/.davfs2/davfs2.conf" << 'EOF'
# davfs2 configuration
use_locks 0
cache_size 50
delay_upload 0
EOF
chown $SERVICE_USER:$SERVICE_USER "/home/$SERVICE_USER/.davfs2/davfs2.conf"
echo "✅ Конфигурация создана: /home/$SERVICE_USER/.davfs2/davfs2.conf"
echo ""

# Update systemd service
echo "🔧 Обновление systemd сервиса..."

# Change ProtectHome to false
sed -i 's/ProtectHome=true/ProtectHome=false/' /etc/systemd/system/cloudtube.service

# Add HOME environment if not exists
if ! grep -q "Environment=\"HOME=" /etc/systemd/system/cloudtube.service; then
    sed -i "/^Environment=\"PATH=/a Environment=\"HOME=/home/$SERVICE_USER\"" /etc/systemd/system/cloudtube.service
    echo "✅ Добавлена переменная HOME"
fi

# Update ReadWritePaths
if grep -q "^ReadWritePaths=" /etc/systemd/system/cloudtube.service; then
    # Remove old ReadWritePaths line
    sed -i '/^ReadWritePaths=/d' /etc/systemd/system/cloudtube.service
fi

# Add new ReadWritePaths after ProtectHome
sed -i "/^ProtectHome=/a ReadWritePaths=/opt/CloudTube/data /opt/CloudTube/logs /opt/CloudTube/temp /home/$SERVICE_USER/.davfs2 /mnt/yandex-disk" /etc/systemd/system/cloudtube.service

echo "✅ Systemd сервис обновлен"
echo ""

# Create mount point if doesn't exist
if [ ! -d /mnt/yandex-disk ]; then
    echo "📁 Создание точки монтирования..."
    mkdir -p /mnt/yandex-disk
    chown $SERVICE_USER:$SERVICE_USER /mnt/yandex-disk
    echo "✅ Точка монтирования создана: /mnt/yandex-disk"
    echo ""
fi

# Reload systemd
echo "🔄 Перезагрузка systemd..."
systemctl daemon-reload
echo "✅ Systemd перезагружен"
echo ""

# Start service
echo "▶️  Запуск сервиса..."
systemctl start cloudtube
sleep 2
echo ""

# Check status
echo "📊 Статус сервиса:"
systemctl status cloudtube --no-pager -l
echo ""

# Show recent logs
echo "📝 Последние логи (проверьте на ошибки):"
journalctl -u cloudtube -n 20 --no-pager
echo ""

echo "=================================="
echo "✅ Исправление завершено!"
echo "=================================="
echo ""
echo "Следующие шаги:"
echo "1. Проверьте, что сервис запущен: sudo systemctl status cloudtube"
echo "2. Откройте Telegram и выполните команду:"
echo "   /connect https://webdav.yandex.ru ваш_email@yandex.ru ваш_oauth_токен"
echo ""
echo "Если нужен OAuth токен:"
echo "   cd /opt/CloudTube"
echo "   source venv/bin/activate"
echo "   python get_yandex_token.py"
echo ""
echo "Документация:"
echo "   - Быстрый старт: /opt/CloudTube/YANDEX_QUICKSTART.md"
echo "   - Полная настройка: /opt/CloudTube/YANDEX_DISK_SETUP.md"
echo "   - Устранение проблем: /opt/CloudTube/UPDATE_WEBDAV_FIX.md"
echo ""
