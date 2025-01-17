# NOCTURN PCA Parser Service

```plaintext
flowchart LR
    A[Main Repo: Click 'Start New Facility'] --> B[New Repo Creation via Template]
    B --> C[GitHub Actions sets up template (ReadMe & config)]
    C --> D[User modifies config.ini, opens PR -> main branch of new repo]
    D --> E[GitHub Actions merges PR, updates README to Step 3]
    E --> F[User sets Windows Shared Folder path, commits]
    F --> G[GitHub Actions checks path, updates README to Step 4]
    G --> H[User flashes Pi, obtains Device Flow code]
    H --> I[Pi device flow authorized, merges into main, updates README to Step 5]
    I --> J[User places .pca in shared folder]
    J --> K[GitHub Actions detects new metadata, triggers Release]
```
A service that monitors directories for PCA files, converts them to JSON, and pushes to GitHub.

## Features

- Monitors both local and network share directories for PCA files
- Automatically converts PCA files to JSON format
- Pushes JSON files to GitHub repository
- Maintains archive of processed files
- Auto-recovery from network disconnections
- Supports Windows sleep/wake cycles
- Automatic SMB remounting
- Detailed logging system

## Quick Installation

One-line installation:
```bash
cd /tmp && git clone -b Test-1-16 https://github.com/johntrue15/NOCTURN-Raspi-test.git && cd NOCTURN-Raspi-test && chmod +x *.sh && sudo ./install.sh
```

## Manual Installation Steps

1. Clone the repository:
```bash
git clone -b Test-1-16 https://github.com/johntrue15/NOCTURN-Raspi-test.git
cd NOCTURN-Raspi-test
```

2. Make scripts executable:
```bash
chmod +x *.sh
```

3. Run installation script:
```bash
sudo ./install.sh
```

## Configuration

The service uses the following configuration files:
- `config.ini`: Main configuration file
- `/root/.smbcredentials`: SMB share credentials
- `/etc/systemd/system/pca_parser.service`: Service configuration

### Directory Structure

```
/opt/pca_parser/
├── input/          # Input directory for PCA files
├── output/         # Output directory for JSON files
├── archive/        # Archive of processed PCA files
└── gitrepo/        # Local Git repository
```

## Monitoring

Check service status:
```bash
sudo systemctl status pca_parser.service
```

View logs:
```bash
sudo tail -f /var/log/pca_parser.log
sudo tail -f /var/log/pca_parser.error.log
```

## Uninstallation

Using uninstall script (includes data backup):
```bash
sudo ./uninstall.sh
```

Quick uninstall (no backup):
```bash
sudo systemctl stop pca_parser.service && sudo systemctl disable pca_parser.service && sudo rm -f /etc/systemd/system/pca_parser.service && sudo systemctl daemon-reload && sudo rm -rf /opt/pca_parser /var/log/pca_parser.* /root/.smbcredentials && sudo sed -i '\#/mnt/windows_share#d' /etc/fstab && sudo umount -f /mnt/windows_share 2>/dev/null || true && sudo rm -rf /mnt/windows_share && echo "Uninstallation complete"
```

## Troubleshooting

1. If service fails to start:
```bash
sudo journalctl -u pca_parser.service -n 50
```

2. Check SMB mount:
```bash
mount | grep windows_share
```

3. Test network connectivity:
```bash
ping -c 3 [WINDOWS_IP]
```

4. Manually restart service:
```bash
sudo systemctl restart pca_parser.service
```

## Recovery Features

- Automatic SMB remounting after network interruptions
- Observer recovery after mount failures
- Multiple SMB protocol version support (3.0, 2.1, 2.0)
- Boot-time network and mount verification
- Periodic mount status checking

## Requirements

- Raspberry Pi with Raspbian/Debian
- Python 3.x
- Git
- SMB/CIFS support
- Network connectivity to Windows share
- GitHub account with personal access token

## Support

For issues or questions, please open an issue on GitHub.
