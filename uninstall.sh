#!/bin/bash
#
# uninstall.sh
#
# Removes the pca_parser service and all its components
set -e  # Exit immediately if a command exits with a non-zero status.

echo "Starting uninstallation of PCA Parser Service..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Function to safely remove files and directories
safe_remove() {
    if [ -e "$1" ]; then
        echo "Removing: $1"
        rm -rf "$1"
    else
        echo "Not found, skipping: $1"
    fi
}

# Stop and disable the service if it exists
echo "Stopping and disabling service..."
if systemctl is-active --quiet pca_parser.service; then
    systemctl stop pca_parser.service
fi
if systemctl is-enabled --quiet pca_parser.service; then
    systemctl disable pca_parser.service
fi

# Remove service file
echo "Removing systemd service file..."
safe_remove "/etc/systemd/system/pca_parser.service"

# Reload systemd to remove the service
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Remove log files
echo "Removing log files..."
safe_remove "/var/log/pca_parser.log"
safe_remove "/var/log/pca_parser.error.log"

# Remove installation directory and all contents
echo "Removing installation directory..."
INSTALL_DIR="/opt/pca_parser"

# Optional: Backup data before removal
if [ -d "$INSTALL_DIR" ]; then
    echo "Creating backup of data before removal..."
    BACKUP_DIR="/opt/pca_parser_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup specific data directories if they exist
    for dir in "input" "output" "archive"; do
        if [ -d "$INSTALL_DIR/$dir" ]; then
            cp -r "$INSTALL_DIR/$dir" "$BACKUP_DIR/"
        fi
    done
    
    echo "Data backed up to: $BACKUP_DIR"
fi

# Remove installation directory
safe_remove "$INSTALL_DIR"

# Optionally remove Python packages (comment out if you want to keep them)
echo "Removing Python packages..."
pip3 uninstall -y gitpython configparser || true

echo "Uninstallation complete!"
echo "Note: A backup of your data has been created at: $BACKUP_DIR"
echo "You can remove this backup directory manually once you've verified you don't need it."
echo "To remove the backup, run: rm -rf $BACKUP_DIR"
