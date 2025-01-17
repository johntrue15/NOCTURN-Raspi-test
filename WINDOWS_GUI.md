# Windows Share Setup (GUI Method)

This guide walks through setting up the Windows shared folder using the graphical interface.

## 1. Create Local User

1. Open **Computer Management**:
   - Right-click Start → Computer Management
   - Or press `Windows + R`, type `compmgmt.msc`

2. Create User Account:
   - Expand **System Tools** → **Local Users and Groups** → **Users**
   - Right-click → **New User**
   - Fill in:
     - User name: `nocturn_share`
     - Password: `your_password`
     - ☑ Password never expires
     - Uncheck "User must change password at next logon"
   - Click **Create**

## 2. Create Shared Folder

1. Create Directory:
   - Create folder: `C:\NOCTURN`
   - Or any preferred location

2. Share the Folder:
   - Right-click folder → **Properties**
   - Go to **Sharing** tab
   - Click **Advanced Sharing**
   - Check **Share this folder**
   - Share name: `NOCTURN`
   - Click **Permissions**

3. Set Share Permissions:
   - Click **Add**
   - Type: `nocturn_share`
   - Click **Check Names** → **OK**
   - Select `nocturn_share`
   - Check **Full Control** under Allow
   - Click **Apply** → **OK**

4. Set Security Permissions:
   - Go to **Security** tab
   - Click **Edit**
   - Click **Add**
   - Type: `nocturn_share`
   - Click **Check Names** → **OK**
   - Select `nocturn_share`
   - Check **Full Control** under Allow
   - Click **Apply** → **OK**

## 3. Network Settings

1. Enable File Sharing:
   - Open **Network and Sharing Center**
   - Click **Change advanced sharing settings**
   - Expand **Private**
   - Select:
     - ☑ Turn on network discovery
     - ☑ Turn on file and printer sharing
   - Click **Save changes**

2. Configure Firewall:
   - Open **Windows Defender Firewall**
   - Click **Allow an app through firewall**
   - Check **File and Printer Sharing** for:
     - ☑ Private
     - ☑ Public (if needed)
   - Click **OK**

## Testing

1. Test Local Access:
   - Open File Explorer
   - Navigate to: `\\localhost\NOCTURN`
   - Should be able to read/write files

2. Test Network Access:
   - From another PC: `\\WINDOWS_IP\NOCTURN`
   - Use credentials:
     - Username: `nocturn_share`
     - Password: `your_password`

## Troubleshooting

1. Share not visible:
   - Verify network discovery is on
   - Check firewall settings
   - Ensure network is set as Private

2. Access denied:
   - Double-check both Share and Security permissions
   - Verify user password
   - Make sure user account is not locked

3. Can't connect:
   - Test using IP address instead of computer name
   - Verify Windows network profile is Private
   - Check if SMB 1.0/2.0 is enabled in Windows Features 