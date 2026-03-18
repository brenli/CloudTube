#!/bin/bash
# Create mount point for CloudTube

set -e

echo "Creating mount point /mnt/cloud_tube..."

# Create directory
sudo mkdir -p /mnt/cloud_tube

# Set ownership to cloudtube user
sudo chown cloudtube:cloudtube /mnt/cloud_tube

# Set permissions
sudo chmod 755 /mnt/cloud_tube

echo "Mount point created successfully!"
echo ""
ls -ld /mnt/cloud_tube

echo ""
echo "Restarting cloudtube service..."
sudo systemctl restart cloudtube

echo ""
echo "Checking logs..."
sleep 2
sudo journalctl -u cloudtube -n 20 --no-pager
