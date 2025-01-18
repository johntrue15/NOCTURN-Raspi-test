# Manual Upload Guide

## Supported File Types
- GE X-ray: `.pca`, `.pcr`, `.pcp`
- North Star: `.rtf`
- [Full list of supported formats](File-Types)

## Upload Process
1. Navigate to the `data/input` directory
2. Upload your log files
3. GitHub Actions will automatically:
   - Convert files to JSON format
   - Generate attestations
   - Create a release with reports
   - Store artifacts

## Example Upload
[Screenshot/GIF of upload process]

## Viewing Results
- Check the Actions tab for conversion status
- Download attestations and reports from Releases
- View JSON data in the `json/` directory 