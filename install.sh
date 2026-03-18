#!/bin/bash 
# CloudTube Installation Script
# Created by Kir
# Requirements: Ubuntu 22.04/24.04

set -e

echo "🎬 CloudTube - Installation Script"
echo "Your YouTube in the Cloud"
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
    git \
    davfs2

echo "✅ System dependencies installed"
echo ""

# Configure davfs2
echo "🔧 Configuring davfs2..."
# Create .davfs2 directory for user
mkdir -p ~/.davfs2
if [ ! -f ~/.davfs2/davfs2.conf ]; then
    cat > ~/.davfs2/davfs2.conf << 'EOF'
# davfs2 configuration
use_locks 0
cache_size 50
delay_upload 0
EOF
    echo "✅ davfs2 configuration created"
fi

# Create mount point
MOUNT_POINT="/mnt/yandex-disk"
if [ ! -d "$MOUNT_POINT" ]; then
    echo "📁 Creating mount point: $MOUNT_POINT"
    sudo mkdir -p "$MOUNT_POINT"
    sudo chown $USER:$USER "$MOUNT_POINT"
    echo "✅ Mount point created"
fi
echo ""

# Create installation directory
INSTALL_DIR="/opt/CloudTube"
echo "📁 Creating installation directory: $INSTALL_DIR"

if [ -d "$INSTALL_DIR" ]; then
    echo "⚠️  Directory already exists. Backing up..."
    sudo mv "$INSTALL_DIR" "$INSTALL_DIR.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Create directory with proper permissions
sudo mkdir -p "$INSTALL_DIR"
sudo chown $USER:$USER "$INSTALL_DIR"

# Clone repository
echo "📥 Cloning CloudTube repository..."
git clone https://github.com/brenli/CloudTube.git "$INSTALL_DIR"

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
mkdir -p "$INSTALL_DIR/data"
mkdir -p "$INSTALL_DIR/logs"
mkdir -p "$INSTALL_DIR/temp"

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

echo ""
echo "📝 Note: Database will be initialized automatically on first run"
echo ""

# Install systemd service
echo "🔧 Installing systemd service..."

# Create cloudtube user home directory if doesn't exist
if [ ! -d "/home/$USER" ]; then
    echo "📁 Creating home directory for user $USER..."
    sudo mkdir -p "/home/$USER"
    sudo chown $USER:$USER "/home/$USER"
fi

# Setup davfs2 for the user
echo "🔧 Setting up davfs2 for user $USER..."
mkdir -p "/home/$USER/.davfs2"
if [ ! -f "/home/$USER/.davfs2/davfs2.conf" ]; then
    cat > "/home/$USER/.davfs2/davfs2.conf" << 'EOF'
# davfs2 configuration
use_locks 0
cache_size 50
delay_upload 0
EOF
    echo "✅ davfs2 configuration created"
fi

sudo cp systemd/cloudtube.service /etc/systemd/system/
sudo sed -i "s|/opt/CloudTube|$INSTALL_DIR|g" /etc/systemd/system/cloudtube.service
sudo sed -i "s|User=cloudtube|User=$USER|g" /etc/systemd/system/cloudtube.service
sudo sed -i "s|/home/cloudtube|/home/$USER|g" /etc/systemd/system/cloudtube.service

sudo systemctl daemon-reload
sudo systemctl enable cloudtube

echo "✅ Systemd service installed"
echo ""

echo "🎉 Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit configuration: nano $INSTALL_DIR/.env"
echo "2. Start the bot: sudo systemctl start cloudtube"
echo "3. Check status: sudo systemctl status cloudtube"
echo "4. View logs: sudo journalctl -u cloudtube -f"
echo ""
echo "For more information, see README.md"
