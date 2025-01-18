# Supported File Types

## GE X-ray Machine Formats
| Extension | Description | Example Data |
|-----------|-------------|--------------|
| `.pca` | Phoenix Scan Parameters | Voltage, Current, FDD |
| `.pcr` | Phoenix Calibration | Detector calibration data |
| `.pcp` | Phoenix Project | Project settings |

## North Star Formats
| Extension | Description | Example Data |
|-----------|-------------|--------------|
| `.rtf` | Rich Text Format | Scan parameters, notes |

## JSON Output Format
All files are converted to a standardized JSON format:
```json
{
  "Voltage": 190,
  "Current": 130,
  "FDD": 802.77534791,
  "FOD": 105.8731875,
  "Magnification": 7.58242353,
  "VoxelSizeX": 0.02637679,
  "VoxelSizeY": 0.02637679
}
``` 