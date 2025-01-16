#!/bin/bash

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root"
    exit 1
fi

# Function to prompt for SMB details
get_smb_details() {
    read -p "Enter Windows PC IP address: " windows_ip
    read -p "Enter Windows share username: " share_user
    read -s -p "Enter Windows share password: " share_password
    echo ""  # New line after password input
    
    # Create credentials file
    echo "username=$share_user" > /root/.smbcredentials
    echo "password=$share_password" >> /root/.smbcredentials
    chmod 600 /root/.smbcredentials
    
    # Create mount point
    mkdir -p /mnt/windows_share
    
    # Add entry to fstab for persistent mount
    echo "Adding mount to /etc/fstab..."
    echo "//$windows_ip/SharedPi /mnt/windows_share cifs credentials=/root/.smbcredentials,iocharset=utf8,file_mode=0777,dir_mode=0777 0 0" >> /etc/fstab
    
    # Try mounting
    echo "Attempting to mount share..."
    mount -a
    
    # Test if mount was successful
    if mount | grep "/mnt/windows_share" > /dev/null; then
        echo "SMB share mounted successfully!"
        return 0
    else
        echo "Failed to mount SMB share. Please check your settings."
        return 1
    fi
}

# Install required packages
echo "Installing required packages..."
apt-get update
apt-get install -y cifs-utils

# Setup SMB share
get_smb_details 