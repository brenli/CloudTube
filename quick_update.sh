#!/bin/bash
# Quick update of webdav.py on server

set -e

echo "Quick update of webdav.py..."

# Stop service
echo "Stopping service..."
sudo systemctl stop cloudtube

# Update code
echo "Updating code..."
sudo cp bot/webdav.py /opt/CloudTube/bot/webdav.py
sudo chown cloudtube:cloudtube /opt/CloudTube/bot/webdav.py

# Ensure mount point exists with any permissions (will be checked after mount)
echo "Ensuring mount point exists..."
sudo mkdir -p /mnt/cloud_tube

# Start service
echo "Starting service..."
sudo systemctl start cloudtube

# Wait and show logs
echo ""
echo "Waiting for service to start..."
sleep 3

echo ""
echo "Recent logs:"
sudo journalctl -u cloudtube -n 30 --no-pager

echo ""
echo "=== Update complete ==="
echo "Watch logs with: sudo journalctl -u cloudtube -f"
