#!/bin/bash
# Test script for Yandex.Disk WebDAV mounting
# Usage: ./test_yandex_mount.sh

set -e

echo "🧪 Тест монтирования Яндекс.Диска"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if davfs2 is installed
echo "1. Проверка davfs2..."
if command -v mount.davfs &> /dev/null; then
    echo -e "${GREEN}✓${NC} davfs2 установлен"
else
    echo -e "${RED}✗${NC} davfs2 не установлен"
    echo "Установите: sudo apt install davfs2"
    exit 1
fi
echo ""

# Check if secrets file exists
echo "2. Проверка учетных данных..."
if [ -f ~/.davfs2/secrets ]; then
    echo -e "${GREEN}✓${NC} Файл ~/.davfs2/secrets существует"
    
    # Check permissions
    perms=$(stat -c "%a" ~/.davfs2/secrets)
    if [ "$perms" = "600" ]; then
        echo -e "${GREEN}✓${NC} Права доступа корректны (600)"
    else
        echo -e "${YELLOW}⚠${NC} Права доступа: $perms (должно быть 600)"
        echo "Исправьте: chmod 600 ~/.davfs2/secrets"
    fi
else
    echo -e "${RED}✗${NC} Файл ~/.davfs2/secrets не найден"
    echo "Создайте файл с учетными данными (см. YANDEX_DISK_SETUP.md)"
    exit 1
fi
echo ""

# Check mount point
echo "3. Проверка точки монтирования..."
MOUNT_POINT="/mnt/yandex-disk"
if [ -d "$MOUNT_POINT" ]; then
    echo -e "${GREEN}✓${NC} Точка монтирования существует: $MOUNT_POINT"
    
    # Check ownership
    owner=$(stat -c "%U:%G" "$MOUNT_POINT")
    current_user="$USER:$USER"
    if [ "$owner" = "$current_user" ]; then
        echo -e "${GREEN}✓${NC} Владелец корректен: $owner"
    else
        echo -e "${YELLOW}⚠${NC} Владелец: $owner (текущий пользователь: $current_user)"
        echo "Исправьте: sudo chown $USER:$USER $MOUNT_POINT"
    fi
else
    echo -e "${YELLOW}⚠${NC} Точка монтирования не существует"
    echo "Создание: sudo mkdir -p $MOUNT_POINT && sudo chown $USER:$USER $MOUNT_POINT"
    sudo mkdir -p "$MOUNT_POINT"
    sudo chown $USER:$USER "$MOUNT_POINT"
    echo -e "${GREEN}✓${NC} Точка монтирования создана"
fi
echo ""

# Check if already mounted
echo "4. Проверка текущего монтирования..."
if mountpoint -q "$MOUNT_POINT"; then
    echo -e "${GREEN}✓${NC} Диск уже примонтирован"
    echo ""
    echo "Содержимое:"
    ls -lh "$MOUNT_POINT" | head -10
    echo ""
    echo "Хотите размонтировать? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        sudo umount "$MOUNT_POINT"
        echo -e "${GREEN}✓${NC} Размонтировано"
    else
        echo "Тест завершен (диск остался примонтированным)"
        exit 0
    fi
else
    echo -e "${YELLOW}⚠${NC} Диск не примонтирован"
fi
echo ""

# Try to mount
echo "5. Попытка монтирования..."
echo "Команда: sudo mount -t davfs https://webdav.yandex.ru $MOUNT_POINT -o uid=$UID,gid=$GID"
echo ""

if sudo mount -t davfs https://webdav.yandex.ru "$MOUNT_POINT" -o uid=$UID,gid=$GID; then
    echo -e "${GREEN}✓${NC} Монтирование успешно!"
    echo ""
    
    # Wait for mount to complete
    sleep 2
    
    # Test access
    echo "6. Проверка доступа..."
    if ls "$MOUNT_POINT" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Доступ к диску работает"
        echo ""
        echo "Содержимое (первые 10 файлов):"
        ls -lh "$MOUNT_POINT" | head -10
        echo ""
        
        # Test write
        echo "7. Проверка записи..."
        test_file="$MOUNT_POINT/cloudtube_test_$(date +%s).txt"
        if echo "CloudTube test file" > "$test_file" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} Запись работает"
            rm -f "$test_file"
            echo -e "${GREEN}✓${NC} Удаление работает"
        else
            echo -e "${RED}✗${NC} Ошибка записи"
        fi
    else
        echo -e "${RED}✗${NC} Ошибка доступа к диску"
    fi
    
    echo ""
    echo "Размонтировать диск? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        sudo umount "$MOUNT_POINT"
        echo -e "${GREEN}✓${NC} Размонтировано"
    else
        echo "Диск остался примонтированным"
    fi
else
    echo -e "${RED}✗${NC} Ошибка монтирования"
    echo ""
    echo "Возможные причины:"
    echo "1. Неверные учетные данные в ~/.davfs2/secrets"
    echo "2. OAuth токен истек (срок действия 1 год)"
    echo "3. Нет доступа к интернету"
    echo "4. Проблемы с правами sudo"
    echo ""
    echo "Получите новый токен: python get_yandex_token.py"
    exit 1
fi

echo ""
echo "=================================="
echo -e "${GREEN}✓${NC} Тест завершен успешно!"
echo "=================================="
echo ""
echo "Теперь вы можете использовать команду в боте:"
echo "/connect https://webdav.yandex.ru ваш_email@yandex.ru ваш_токен"
