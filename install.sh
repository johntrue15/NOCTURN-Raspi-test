#!/bin/bash
#
# install.sh
#
# Installs the pca_parser systemd service from this repo.

set -e  # Exit immediately if a command exits with a non-zero status.

echo "Installing dependencies..."
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip git

echo "Installing Python libraries (gitpython, configparser)..."
sudo pip3 install gitpython configparser

# Define install directory
INSTALL_DIR="/opt/pca_parser"

# Copy files to /opt/pca_parser
echo "Creating $INSTALL_DIR..."
sudo mkdir -p "$INSTALL_DIR"

echo "Copying files to $INSTALL_DIR..."
# Adjust as needed if you have more files
sudo cp pca_parser.py "$INSTALL_DIR/pca_parser.py"
sudo cp config.ini "$INSTALL_DIR/config.ini"
sudo chmod +x "$INSTALL_DIR/pca_parser.py"

# Create systemd service file
echo "Creating systemd service at /etc/systemd/system/pca_parser.service..."
SERVICE_FILE="/etc/systemd/system/pca_parser.service"
sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=PCA Parser Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $INSTALL_DIR/pca_parser.py
Restart=always
RestartSec=10
WorkingDirectory=$INSTALL_DIR

[Install]
WantedBy=multi-user.target
EOF

echo "Reloading systemd..."
sudo systemctl daemon-reload

echo "Enabling pca_parser service..."
sudo systemctl enable pca_parser.service

echo "Starting pca_parser service..."
sudo systemctl start pca_parser.service

echo "Installation complete!"
echo "Service status:"
sudo systemctl status pca_parser.service --no-pager
