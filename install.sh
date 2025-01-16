#!/bin/bash
#
# install.sh
#
# Installs the pca_parser systemd service
set -e  # Exit immediately if a command exits with a non-zero status.

echo "Starting installation of PCA Parser Service..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

echo "Installing system dependencies..."
apt-get update -y
apt-get install -y python3 python3-pip git

echo "Installing Python dependencies..."
pip3 install gitpython configparser

# Define installation directory and create structure
INSTALL_DIR="/opt/pca_parser"
echo "Creating directory structure in $INSTALL_DIR..."

# Create all required directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/input"
mkdir -p "$INSTALL_DIR/output"
mkdir -p "$INSTALL_DIR/archive"
mkdir -p "$INSTALL_DIR/gitrepo"

# Set proper permissions
chown -R root:root "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR"

echo "Copying program files..."
cp pca_parser.py "$INSTALL_DIR/pca_parser.py"
cp config.ini "$INSTALL_DIR/config.ini"
chmod +x "$INSTALL_DIR/pca_parser.py"

# Create systemd service file
echo "Creating systemd service..."
cat > /etc/systemd/system/pca_parser.service << 'EOF'
[Unit]
Description=PCA Parser Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/pca_parser/pca_parser.py
Restart=always
RestartSec=10
WorkingDirectory=/opt/pca_parser
User=root
Group=root
StandardOutput=append:/var/log/pca_parser.log
StandardError=append:/var/log/pca_parser.error.log
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Create log files and set permissions
touch /var/log/pca_parser.log
touch /var/log/pca_parser.error.log
chmod 644 /var/log/pca_parser.log
chmod 644 /var/log/pca_parser.error.log

echo "Reloading systemd daemon..."
systemctl daemon-reload

echo "Setting up GitHub configurations..."
chmod +x setup_git_config.sh
./setup_git_config.sh

# If setup_git_config.sh fails, stop the installation
if [ $? -ne 0 ]; then
    echo "GitHub configuration failed. Please check the errors and try again."
    exit 1
fi

echo "Setting up SMB share..."
chmod +x setup_smb_share.sh
./setup_smb_share.sh

# If setup_smb_share.sh fails, ask user if they want to continue
if [ $? -ne 0 ]; then
    read -p "SMB share setup failed. Continue with local-only installation? (y/n) " answer
    if [ "$answer" != "y" ]; then
        echo "Installation aborted."
        exit 1
    else
        # Update config to disable shared drive
        sed -i 's/enabled = true/enabled = false/' "$INSTALL_DIR/config.ini"
    fi
fi

echo "Enabling and starting service..."
systemctl enable pca_parser.service
systemctl start pca_parser.service

echo "Installation complete!"
echo "You can monitor the service using:"
echo "  systemctl status pca_parser.service"
echo "  journalctl -u pca_parser.service -f"
echo "Log files are located at:"
echo "  /var/log/pca_parser.log"
echo "  /var/log/pca_parser.error.log"
