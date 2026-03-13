# Contributing to CloudTube

First off, thank you for considering contributing to CloudTube! 🎉

## 👨‍💻 About the Project

CloudTube is created and maintained by **Kir**. It's a Telegram bot that makes it easy to download YouTube videos to your WebDAV storage.

## 🤝 How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, etc.)
- Logs (without sensitive information!)

### Suggesting Features

Have an idea? Great! Open an issue with:
- Clear description of the feature
- Why it would be useful
- How it should work

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings
- Add tests for new features
- Keep it simple and readable

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=bot --cov-report=html

# Run specific test
pytest tests/test_download.py
```

## 📝 Development Setup

```bash
# Clone the repo
git clone https://github.com/Kir-dev/CloudTube.git
cd CloudTube

# Setup development environment
./setup.sh  # Linux/Mac
.\setup.bat  # Windows

# Install dev dependencies
pip install -r requirements.txt

# Run tests
pytest
```

## 🎯 Areas for Contribution

- 🐛 Bug fixes
- ✨ New features
- 📝 Documentation improvements
- 🌍 Translations
- 🧪 More tests
- 🎨 UI/UX improvements

## 📜 Code of Conduct

- Be respectful and inclusive
- Help others learn and grow
- Focus on constructive feedback
- Have fun! 🎉

## 💬 Questions?

Feel free to open an issue or reach out to Kir.

## 🙏 Thank You!

Every contribution, no matter how small, is appreciated!

---

**CloudTube** - Your YouTube in the Cloud
Created with ❤️ by Kir
