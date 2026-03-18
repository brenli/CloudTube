#!/bin/bash
# Fix cloudtube user home directory and mount point permissions

set -e

echo "Fixing cloudtube user home directory..."

# Create /home/cloudtube if it doesn't exist
if [ ! -d "/home/cloudtube" ]; then
    echo "Creating /home/cloudtube directory..."
    sudo mkdir -p /home/cloudtube
fi

# Set ownership to cloudtube user
echo "Setting ownership to cloudtube user..."
sudo chown -R cloudtube:cloudtube /home/cloudtube

# Set proper permissions
echo "Setting permissions..."
sudo chmod 755 /home/cloudtube

# Create .davfs2 directory if needed
if [ ! -d "/home/cloudtube/.davfs2" ]; then
    echo "Creating /home/cloudtube/.davfs2 directory..."
    sudo mkdir -p /home/cloudtube/.davfs2
    sudo chown cloudtube:cloudtube /home/cloudtube/.davfs2
    sudo chmod 700 /home/cloudtube/.davfs2
fi

echo "Done! Home directory structure:"
ls -la /home/cloudtube/

echo ""
echo "Creating mount point /mnt/cloud_tube..."

# Create mount point if it doesn't exist
if [ ! -d "/mnt/cloud_tube" ]; then
    sudo mkdir -p /mnt/cloud_tube
fi

# Set ownership and permissions
sudo chown cloudtube:cloudtube /mnt/cloud_tube
sudo chmod 755 /mnt/cloud_tube

echo "Mount point created and configured:"
ls -ld /mnt/cloud_tube

echo ""
echo "Reloading systemd configuration..."
sudo systemctl daemon-reload

echo "Restarting cloudtube service..."
sudo systemctl restart cloudtube

echo "Checking service status..."
sleep 2
sudo systemctl status cloudtube --no-pager -l
