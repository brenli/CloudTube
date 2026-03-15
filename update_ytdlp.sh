#!/bin/bash

# Update yt-dlp script for CloudTube
# This script updates yt-dlp to the latest version and restarts the bot

set -e

echo "🔄 Updating yt-dlp to latest version..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Update yt-dlp
pip install --upgrade yt-dlp

echo "✅ yt-dlp updated successfully!"
echo ""
echo "Current yt-dlp version:"
yt-dlp --version

echo ""
echo "🔄 Restarting CloudTube service..."

# Check if running as systemd service
if systemctl is-active --quiet cloudtube; then
    sudo systemctl restart cloudtube
    echo "✅ CloudTube service restarted!"
    echo ""
    echo "Check status with: sudo systemctl status cloudtube"
else
    echo "⚠️  CloudTube service not found or not running"
    echo "If you're running the bot manually, please restart it now"
fi
