# Development Guide

## Project Structure
```
.
├── .github/
│   ├── workflows/          # GitHub Actions workflows
│   │   ├── file-processor.yml
│   │   └── ci.yml
│   └── scripts/           # Conversion scripts
│       └── pca_to_json.py
├── data/
│   ├── input/            # Raw log files
│   └── output/           # Converted JSON
├── tests/                # Test suite
└── install/              # Raspberry Pi setup
```

## Adding New File Types
1. Create converter in `.github/scripts/`
2. Add file type to workflow triggers
3. Update documentation
4. Add tests

## Testing
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Check code style
flake8 .
black .
```

## Attestation Development
- Uses GitHub's attestation API
- Sigstore for signing
- In-toto format for predicates 