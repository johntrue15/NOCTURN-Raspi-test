#!/bin/bash

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root"
    exit 1
fi

# Add at the beginning after root check
echo "Verifying SMB dependencies..."
if ! command -v mount.cifs >/dev/null 2>&1; then
    echo "Installing cifs-utils..."
    apt-get update
    apt-get install -y cifs-utils
fi

if ! command -v smbclient >/dev/null 2>&1; then
    echo "Installing smbclient..."
    apt-get install -y smbclient
fi

if ! pip3 show watchdog >/dev/null 2>&1; then
    echo "Installing watchdog..."
    pip3 install watchdog
fi

# Function to prompt for SMB details
get_smb_details() {
    # Debug output to verify IP
    read -p "Enter Windows PC IP address: " windows_ip
    echo "Debug: Using IP address: $windows_ip"
    
    # Get Windows credentials
    read -p "Enter Windows username (nocturn_share): " win_user
    read -s -p "Enter Windows password: " win_pass
    echo ""
    
    # Create mount point
    mkdir -p /mnt/windows_share
    
    # Remove any existing entry for this mount point
    sed -i '\#/mnt/windows_share#d' /etc/fstab
    
    # Create credentials file with proper escaping
    printf "username=%s\npassword=%s\n" "$win_user" "$win_pass" > /root/.smbcredentials
    chmod 600 /root/.smbcredentials
    
    # Try different mount options
    echo "Trying different mount options..."
    
    # Array of different mount options to try
    MOUNT_OPTIONS=(
        "vers=2.0,credentials=/root/.smbcredentials,iocharset=utf8,dir_mode=0777,file_mode=0777,notify"
        "vers=3.0,credentials=/root/.smbcredentials,iocharset=utf8,dir_mode=0777,file_mode=0777,notify"
        "vers=2.1,credentials=/root/.smbcredentials,iocharset=utf8,dir_mode=0777,file_mode=0777,notify"
    )
    
    # Try each mount option
    for options in "${MOUNT_OPTIONS[@]}"; do
        echo "Trying mount with options: $options"
        # Always try to unmount first
        echo "Unmounting any existing share..."
        umount /mnt/windows_share 2>/dev/null || true
        
        if mount -t cifs "//$windows_ip/NOCTURN" /mnt/windows_share -o "$options" 2>/dev/null; then
            echo "Mount successful with options: $options"
            # Add successful mount to fstab using printf to handle special characters
            printf "//$windows_ip/NOCTURN /mnt/windows_share cifs %s 0 0\n" "$options" >> /etc/fstab
            return 0
        else
            echo "Mount failed with these options"
            dmesg | tail -n 3
        fi
    done
    
    echo "All mount attempts failed. Please check Windows sharing settings:"
    echo "1. Ensure the folder is shared"
    echo "2. Check share permissions (nocturn_share - Full Control)"
    echo "3. Check NTFS permissions (nocturn_share - Full Control)"
    echo "4. Check Windows Defender Firewall settings"
    return 1
}

# Install required packages
echo "Installing required packages..."
apt-get update
apt-get install -y cifs-utils smbclient

# Add at the end of the script, before get_smb_details is called

verify_mount() {
    echo "Verifying mount..."
    if mount | grep -q "windows_share"; then
        echo "✓ Share mounted successfully"
        echo "Mount details:"
        mount | grep "windows_share"
        echo "Directory contents:"
        ls -l /mnt/windows_share
        return 0
    else
        echo "✗ Share mount verification failed"
        return 1
    fi
}

# Setup SMB share
if get_smb_details; then
    verify_mount
else
    echo "SMB setup failed"
    exit 1
fi 