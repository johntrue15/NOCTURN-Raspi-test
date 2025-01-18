# Raspberry Pi Installation Guide

## Prerequisites
- Raspberry Pi (3B+ or newer recommended)
- SD Card (16GB+ recommended)
- Network connection to X-ray machine
- GitHub account

## Quick Install
1. Download NOCTURN.iso
2. Flash to SD card using Raspberry Pi Imager
3. Boot Raspberry Pi
4. Follow GitHub authentication flow

## Manual Installation Steps
```bash
# 1. Clone the repository
git clone https://github.com/johntrue15/NOCTURN-Raspi-test.git
cd NOCTURN-Raspi-test

# 2. Run installation script
sudo ./install.sh

# 3. Configure GitHub credentials
sudo ./setup_git_config.sh

# 4. Setup network share
sudo ./setup_smb_share.sh
```

## Configuration Files
- `/opt/pca_parser/config.ini`: Main configuration
- `/root/.git-credentials`: GitHub authentication
- `/etc/systemd/system/pca_parser.service`: Service configuration

## Verifying Installation
1. Check service status:
   ```bash
   systemctl status pca_parser.service
   ```
2. Monitor logs:
   ```bash
   journalctl -u pca_parser.service -f
   ``` 