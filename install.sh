#!/bin/bash
# YouTube WebDAV Bot Installation Script
# Requirements: 14.4, 14.5, 14.6

set -e

echo "🎬 YouTube WebDAV Bot - Installation Script"
echo "==========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please do not run this script as root"
    exit 1
fi

# Check OS
if [ ! -f /etc/os-release ]; then
    echo "❌ Cannot detect OS. This script supports Ubuntu 22/24 only."
    exit 1
fi

. /etc/os-release
if [[ "$ID" != "ubuntu" ]] || [[ ! "$VERSION_ID" =~ ^(22|24) ]]; then
    echo "❌ This script supports Ubuntu 22.04 or 24.04 only"
    echo "   Detected: $PRETTY_NAME"
    exit 1
fi

echo "✅ OS: $PRETTY_NAME"
echo ""

# Check Python version
if ! command -v python3.11 &> /dev/null; then
    echo "📦 Installing Python 3.11..."
    sudo apt update
    sudo apt install -y software-properties-common
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install -y python3.11 python3.11-venv python3.11-dev
fi

PYTHON_VERSION=$(python3.11 --version | cut -d' ' -f2)
echo "✅ Python: $PYTHON_VERSION"
echo ""

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt install -y \
    python3-pip \
    ffmpeg \
    sqlite3 \
    git

echo "✅ System dependencies installed"
echo ""

# Create installation directory
INSTALL_DIR="/opt/youtube-webdav-bot"
echo "📁 Creating installation directory: $INSTALL_DIR"

if [ -d "$INSTALL_DIR" ]; then
    echo "⚠️  Directory already exists. Backing up..."
    sudo mv "$INSTALL_DIR" "$INSTALL_DIR.backup.$(date +%Y%m%d_%H%M%S)"
fi

sudo mkdir -p "$INSTALL_DIR"
sudo chown $USER:$USER "$INSTALL_DIR"

# Copy files
echo "📋 Copying files..."
cp -r . "$INSTALL_DIR/"
cd "$INSTALL_DIR"

# Create virtual environment
echo "🐍 Creating virtual environment..."
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "✅ Python dependencies installed"
echo ""

# Create data directories
echo "📁 Creating data directories..."
sudo mkdir -p /var/lib/youtube-webdav-bot
sudo mkdir -p /var/log/youtube-webdav-bot
sudo mkdir -p /tmp/youtube-webdav-bot

sudo chown $USER:$USER /var/lib/youtube-webdav-bot
sudo chown $USER:$USER /var/log/youtube-webdav-bot
sudo chown $USER:$USER /tmp/youtube-webdav-bot

echo "✅ Data directories created"
echo ""

# Create .env file
if [ ! -f .env ]; then
    echo "⚙️  Creating .env configuration file..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your configuration:"
    echo "   - TELEGRAM_BOT_TOKEN"
    echo "   - TELEGRAM_OWNER_ID"
    echo ""
else
    echo "✅ .env file already exists"
    echo ""
fi

# Initialize database
echo "🗄️  Initializing database..."
python3 -c "
import asyncio
from bot.database import Database
from bot.config import AppConfig

async def init():
    config = AppConfig.load_from_env()
    db = Database(config.database_path)
    await db.initialize()
    await db.close()
    print('✅ Database initialized')

asyncio.run(init())
"

# Install systemd service
echo "🔧 Installing systemd service..."
sudo cp systemd/youtube-webdav-bot.service /etc/systemd/system/
sudo sed -i "s|/opt/youtube-webdav-bot|$INSTALL_DIR|g" /etc/systemd/system/youtube-webdav-bot.service
sudo sed -i "s|User=youtube-bot|User=$USER|g" /etc/systemd/system/youtube-webdav-bot.service

sudo systemctl daemon-reload
sudo systemctl enable youtube-webdav-bot

echo "✅ Systemd service installed"
echo ""

echo "🎉 Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit configuration: nano $INSTALL_DIR/.env"
echo "2. Start the bot: sudo systemctl start youtube-webdav-bot"
echo "3. Check status: sudo systemctl status youtube-webdav-bot"
echo "4. View logs: sudo journalctl -u youtube-webdav-bot -f"
echo ""
echo "For more information, see README.md"
