# Windows Share Setup Guide

This guide explains how to set up a shared folder on Windows for use with the PCA Parser service.

## 1. Create a Dedicated User

1. Open Command Prompt as Administrator
2. Create a new user:
   ```cmd
   net user nocturn_share Nocturn123! /add
   ```

3. Add user to necessary groups:
   ```cmd
   net localgroup "Users" nocturn_share /add
   ```

4. Make the password never expire:
   ```cmd
   wmic useraccount where "Name='nocturn_share'" set PasswordExpires=false
   ```

## 2. Create and Share the Folder

1. Create a new folder (e.g., `C:\PCA_Share`)

2. Right-click the folder → Properties → Sharing tab → Advanced Sharing

3. Check "Share this folder"

4. Click "Permissions"
   - Remove "Everyone" if present
   - Add "nocturn_share"
   - Grant "Full Control" to nocturn_share

5. Click "Apply" and "OK"

## 3. Set NTFS Permissions

1. Still in Properties → Security tab → Edit

2. Add "nocturn_share" if not present
   - Click "Add"
   - Enter "nocturn_share"
   - Click "Check Names"
   - Click "OK"

3. Select "nocturn_share" and grant these permissions:
   - Full control
   - Modify
   - Read & execute
   - List folder contents
   - Read
   - Write

4. Click "Apply" and "OK"

## 4. Configure Network Settings

1. Open Windows Defender Firewall with Advanced Security

2. Ensure these inbound rules are enabled:
   - File and Printer Sharing (SMB-In)
   - File and Printer Sharing (NB-Session-In)

3. Open Network and Sharing Center:
   - Click "Change advanced sharing settings"
   - Expand "Private"
   - Enable "Turn on network discovery"
   - Enable "Turn on file and printer sharing"
   - Save changes

## 5. Test the Share

1. From another Windows PC:
   ```
   net use \\COMPUTER-NAME\PCA_Share /user:nocturn_share Nocturn123!
   ```

2. Or map network drive:
   - Open File Explorer
   - Right-click "Network"
   - Click "Map network drive"
   - Drive: `Z:`
   - Folder: `\\COMPUTER-NAME\PCA_Share`
   - Check "Connect using different credentials"
   - Enter username: `nocturn_share`
   - Enter password: `Nocturn123!`

## Troubleshooting

1. If connection fails:
   - Verify Windows PC and Raspberry Pi are on same network
   - Check Windows PC firewall settings
   - Ensure SMB 1.0/CIFS is enabled in Windows Features
   - Try using IP address instead of computer name

2. Permission issues:
   - Double-check both share and NTFS permissions
   - Verify user account is not locked
   - Test local access with nocturn_share account

3. Network issues:
   - Test connectivity: `ping COMPUTER-NAME`
   - Verify SMB ports are open: `netstat -an | find "445"`
   - Check Network Discovery is enabled

## Security Notes

- The shared folder should only contain PCA files for processing
- Regularly change the password for nocturn_share
- Consider using a more restricted network segment
- Monitor access logs for unauthorized attempts 