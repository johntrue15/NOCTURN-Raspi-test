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
    
    # Try different connection methods
    echo "Testing connection methods..."
    
    # Method 1: Basic connection test
    echo "Testing basic connection..."
    if ping -c 1 $windows_ip >/dev/null 2>&1; then
        echo "Network connection successful"
    else
        echo "Network connection failed"
        return 1
    fi
    
    # Method 2: List shares with different protocols
    echo "Attempting to list shares (SMB1)..."
    smbclient -L $windows_ip -N -m SMB1
    echo "Attempting to list shares (SMB2)..."
    smbclient -L $windows_ip -N -m SMB2
    echo "Attempting to list shares (SMB3)..."
    smbclient -L $windows_ip -N -m SMB3
    
    # Try different mount options
    echo "Trying different mount options..."
    
    # Array of different mount options to try
    MOUNT_OPTIONS=(
        "vers=1.0,guest,noperm,rw,iocharset=utf8"
        "vers=2.0,guest,noperm,rw,iocharset=utf8"
        "vers=3.0,guest,noperm,rw,iocharset=utf8"
        "vers=1.0,guest,sec=none,noperm,rw"
        "vers=2.0,guest,sec=none,noperm,rw"
        "vers=3.0,guest,sec=none,noperm,rw"
    )
    
    # Try each mount option
    for options in "${MOUNT_OPTIONS[@]}"; do
        echo "Trying mount with options: $options"
        if mount -t cifs "//$windows_ip/nocturn" /mnt/windows_share -o "$options" 2>/dev/null; then
            echo "Mount successful with options: $options"
            # Add successful mount to fstab
            echo "//$windows_ip/nocturn /mnt/windows_share cifs $options 0 0" >> /etc/fstab
            return 0
        else
            echo "Mount failed with these options"
            dmesg | tail -n 3
        fi
        # Cleanup
        umount /mnt/windows_share 2>/dev/null || true
    done
    
    echo "All mount attempts failed. Please check Windows sharing settings:"
    echo "1. Ensure the folder is shared"
    echo "2. Check share permissions (Everyone - Full Control)"
    echo "3. Check NTFS permissions (Everyone - Full Control)"
    echo "4. Check Windows Defender Firewall settings"
    return 1
}

# Install required packages
echo "Installing required packages..."
apt-get update
apt-get install -y cifs-utils smbclient

# Setup SMB share
get_smb_details 