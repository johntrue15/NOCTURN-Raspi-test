# Contributing to NOCTURN PCA Parser

## Development Setup

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # Linux
```

2. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

## Code Style

- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to functions and classes
- Keep functions focused and small
- Comment complex logic

## Testing

1. Run tests:
```bash
pytest tests/
```

2. Check code style:
```bash
flake8 .
black .
```

## Pull Request Process

1. Create feature branch from `develop`
2. Add tests for new functionality
3. Update documentation
4. Run test suite
5. Submit PR with description

## Commit Messages

Format:
```
type(scope): description

[optional body]
```

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- style: Formatting
- refactor: Code restructuring
- test: Adding tests
- chore: Maintenance 