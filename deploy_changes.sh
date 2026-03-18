#!/bin/bash
# Deploy changes to the server

set -e

echo "=== Deploying CloudTube changes ==="
echo ""

# Check if we're on the server
if [ ! -d "/opt/CloudTube" ]; then
    echo "Error: /opt/CloudTube not found. Are you on the server?"
    exit 1
fi

echo "Step 1: Stopping cloudtube service..."
sudo systemctl stop cloudtube

echo ""
echo "Step 2: Backing up current webdav.py..."
sudo cp /opt/CloudTube/bot/webdav.py /opt/CloudTube/bot/webdav.py.backup.$(date +%Y%m%d_%H%M%S)

echo ""
echo "Step 3: Copying new webdav.py..."
sudo cp bot/webdav.py /opt/CloudTube/bot/webdav.py
sudo chown cloudtube:cloudtube /opt/CloudTube/bot/webdav.py

echo ""
echo "Step 4: Updating systemd service file..."
sudo cp systemd/cloudtube.service /etc/systemd/system/cloudtube.service

echo ""
echo "Step 5: Setting up sudoers for cloudtube user..."
sudo cp cloudtube-sudoers /etc/sudoers.d/cloudtube
sudo chmod 440 /etc/sudoers.d/cloudtube
sudo visudo -c || {
    echo "Error: sudoers syntax check failed!"
    sudo rm /etc/sudoers.d/cloudtube
    exit 1
}
echo "Sudoers configuration validated and installed"

echo ""
echo "Step 6: Creating /home/cloudtube if needed..."
if [ ! -d "/home/cloudtube" ]; then
    sudo mkdir -p /home/cloudtube
    sudo chown cloudtube:cloudtube /home/cloudtube
    sudo chmod 755 /home/cloudtube
fi

echo ""
echo "Step 7: Creating /home/cloudtube/.davfs2..."
if [ ! -d "/home/cloudtube/.davfs2" ]; then
    sudo mkdir -p /home/cloudtube/.davfs2
    sudo chown cloudtube:cloudtube /home/cloudtube/.davfs2
    sudo chmod 700 /home/cloudtube/.davfs2
fi

echo ""
echo "Step 8: Creating /mnt/cloud_tube..."
if [ ! -d "/mnt/cloud_tube" ]; then
    sudo mkdir -p /mnt/cloud_tube
fi
sudo chown cloudtube:cloudtube /mnt/cloud_tube
sudo chmod 755 /mnt/cloud_tube

echo ""
echo "Step 9: Reloading systemd configuration..."
sudo systemctl daemon-reload

echo ""
echo "Step 10: Starting cloudtube service..."
sudo systemctl start cloudtube

echo ""
echo "Step 11: Checking service status..."
sleep 3
sudo systemctl status cloudtube --no-pager -l

echo ""
echo "=== Deployment complete! ==="
echo ""
echo "Check logs with: sudo journalctl -u cloudtube -f"
