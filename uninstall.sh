#!/bin/bash
#
# uninstall.sh
#
# Stops and removes the pca_parser systemd service, and deletes /opt/pca_parser

set -e

SERVICE="pca_parser.service"
INSTALL_DIR="/opt/pca_parser"

echo "Stopping $SERVICE..."
sudo systemctl stop $SERVICE || true

echo "Disabling $SERVICE..."
sudo systemctl disable $SERVICE || true

echo "Removing service file..."
sudo rm -f /etc/systemd/system/$SERVICE

echo "Reloading systemd..."
sudo systemctl daemon-reload
sudo systemctl reset-failed

echo "Removing $INSTALL_DIR..."
sudo rm -rf "$INSTALL_DIR"

echo "Uninstallation complete!"
