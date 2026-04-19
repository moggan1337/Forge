# Contributing to Forge

Thank you for your interest in contributing to Forge!

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Forge.git
   cd Forge
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate  # Windows
   ```

4. Install dependencies:
   ```bash
   pip install -e ".[dev,test]"
   ```

5. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Code Style

- Follow PEP 8 for Python code
- Use type hints throughout
- Keep lines under 100 characters
- Use meaningful variable names

## Testing

Run tests with:
```bash
pytest
```

With coverage:
```bash
pytest --cov=forge --cov-report=html
```

## Pull Request Process

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit:
   ```bash
   git commit -m "Add your feature"
   ```

3. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Open a Pull Request on GitHub

## Reporting Issues

Please use GitHub Issues to report bugs or request features. Include:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Python version, OS, etc.)

## Questions?

Feel free to open an issue for any questions!
