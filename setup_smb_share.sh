#!/bin/bash

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root"
    exit 1
fi

# Function to prompt for SMB details
get_smb_details() {
    # Debug output to verify IP
    read -p "Enter Windows PC IP address: " windows_ip
    echo "Debug: Using IP address: $windows_ip"
    
    # Create mount point
    mkdir -p /mnt/windows_share
    
    # Remove any existing entry for this mount point
    sed -i '\#/mnt/windows_share#d' /etc/fstab
    
    # First, try to list available shares for debugging
    echo "Attempting to list available shares..."
    smbclient -L $windows_ip -N
    
    # Add entry to fstab for persistent mount
    echo "Adding mount to /etc/fstab..."
    MOUNT_LINE="//$windows_ip/nocturn /mnt/windows_share cifs vers=2.0,guest,noperm,rw,iocharset=utf8,file_mode=0777,dir_mode=0777 0 0"
    echo "Debug: Mount line: $MOUNT_LINE"
    echo "$MOUNT_LINE" >> /etc/fstab
    
    # Try mounting
    echo "Attempting to mount share..."
    umount /mnt/windows_share 2>/dev/null || true
    mount -a
    
    # Test if mount was successful
    if mount | grep "/mnt/windows_share" > /dev/null; then
        echo "SMB share mounted successfully!"
        return 0
    else
        echo "Failed to mount SMB share. Please check your settings."
        echo "Trying direct mount command for debugging..."
        mount -t cifs "//$windows_ip/nocturn" /mnt/windows_share -o vers=2.0,guest,noperm,rw
        dmesg | tail -n 5  # Show recent kernel messages for debugging
        return 1
    fi
}

# Install required packages
echo "Installing required packages..."
apt-get update
apt-get install -y cifs-utils smbclient

# Setup SMB share
get_smb_details 