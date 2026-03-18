#!/bin/bash
# Check if deployment was successful

echo "=== Checking CloudTube deployment ==="
echo ""

echo "1. Checking MOUNT_POINT in code:"
grep "MOUNT_POINT = " /opt/CloudTube/bot/webdav.py || echo "❌ File not found or pattern not found"

echo ""
echo "2. Checking /home/cloudtube/.davfs2:"
ls -ld /home/cloudtube/.davfs2 2>/dev/null || echo "❌ Directory not found"

echo ""
echo "3. Checking /mnt/cloud_tube:"
ls -ld /mnt/cloud_tube 2>/dev/null || echo "❌ Directory not found"

echo ""
echo "4. Checking systemd service file:"
grep "ReadWritePaths" /etc/systemd/system/cloudtube.service || echo "❌ Service file not found"

echo ""
echo "5. Checking service status:"
sudo systemctl is-active cloudtube

echo ""
echo "6. Last 10 log lines:"
sudo journalctl -u cloudtube -n 10 --no-pager

echo ""
echo "=== Check complete ==="
