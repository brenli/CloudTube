#!/bin/bash
# Fix permissions on mount point

set -e

echo "Fixing permissions on /mnt/cloud_tube..."

# Set ownership to cloudtube user
sudo chown cloudtube:cloudtube /mnt/cloud_tube

# Set permissions
sudo chmod 755 /mnt/cloud_tube

echo "Permissions fixed!"
echo ""
echo "Current permissions:"
ls -ld /mnt/cloud_tube

echo ""
echo "Testing write access as cloudtube user..."
sudo -u cloudtube touch /mnt/cloud_tube/test_write 2>/dev/null && {
    echo "✅ Write access OK"
    sudo -u cloudtube rm /mnt/cloud_tube/test_write
} || {
    echo "❌ Still no write access"
    echo "Checking ownership..."
    stat /mnt/cloud_tube
}

echo ""
echo "Restarting cloudtube service..."
sudo systemctl restart cloudtube

echo ""
echo "Waiting for service to start..."
sleep 3

echo ""
echo "Checking logs..."
sudo journalctl -u cloudtube -n 30 --no-pager
