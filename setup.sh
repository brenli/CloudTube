#!/bin/bash
# Setup script for CloudTube (Linux/Mac)
# Created by Kir
# Requirements: Python 3.11+, FFmpeg

set -e

echo "============================================"
echo "CloudTube - Setup Script"
echo "Your YouTube in the Cloud"
echo "============================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD=python3.11
elif command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
else
    echo -e "${RED}ERROR: Python 3.11+ is not installed${NC}"
    echo "Please install Python 3.11 or higher"
    exit 1
fi

python_version=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓${NC} Python version: $python_version"
echo ""

# Check FFmpeg
echo "Checking FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    ffmpeg_version=$(ffmpeg -version 2>&1 | head -n1 | awk '{print $3}')
    echo -e "${GREEN}✓${NC} FFmpeg version: $ffmpeg_version"
else
    echo -e "${YELLOW}WARNING: FFmpeg is not installed${NC}"
    echo "The bot will not work without FFmpeg!"
    echo "Install it with: sudo apt install ffmpeg (Ubuntu/Debian)"
    echo "                 brew install ffmpeg (Mac)"
    echo ""
fi
echo ""

# Check davfs2 (for WebDAV mounting)
echo "Checking davfs2..."
if command -v mount.davfs &> /dev/null; then
    echo -e "${GREEN}✓${NC} davfs2 is installed"
else
    echo -e "${YELLOW}WARNING: davfs2 is not installed${NC}"
    echo "davfs2 is required for Yandex.Disk WebDAV mounting"
    echo "Install it with: sudo apt install davfs2 (Ubuntu/Debian)"
    echo ""
fi
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists, skipping..."
else
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip
echo ""

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt
echo -e "${GREEN}✓${NC} Dependencies installed"
echo ""

# Create directories
echo "Creating directories..."
mkdir -p data logs temp
chmod 755 data logs temp
echo -e "${GREEN}✓${NC} Directories created: data, logs, temp"
echo ""

# Create .env file
if [ -f ".env" ]; then
    echo ".env file already exists, skipping..."
else
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo -e "${YELLOW}IMPORTANT: Please edit .env file and fill in your configuration:${NC}"
    echo "  - TELEGRAM_BOT_TOKEN (get from @BotFather)"
    echo "  - TELEGRAM_OWNER_ID (get from @userinfobot)"
    echo ""
    echo "Edit now? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        ${EDITOR:-nano} .env
    fi
fi
echo ""

# Initialize database
echo "Initializing database..."
python -c "
import asyncio
from bot.database import Database
from bot.config import AppConfig

async def init():
    try:
        config = AppConfig.load_from_env()
        db = Database(config.database_path)
        await db.initialize()
        await db.close()
        print('✓ Database initialized successfully')
    except Exception as e:
        print(f'Database will be initialized on first run: {e}')

asyncio.run(init())
" 2>/dev/null || echo "Database will be initialized on first run"
echo ""

echo "============================================"
echo -e "${GREEN}Setup complete!${NC}"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Edit .env file with your configuration (if not done yet):"
echo "     nano .env"
echo ""
echo "  2. Activate virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  3. Run the bot:"
echo "     python -m bot.main"
echo ""
echo "Useful commands:"
echo "  - Run tests: pytest"
echo "  - Check configuration: python -c 'from bot.config import AppConfig; AppConfig.load_from_env()'"
echo "  - View logs: tail -f logs/bot.log"
echo ""
echo "For production deployment, see INSTALLATION.md"
echo ""
