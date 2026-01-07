# Contributing to Polymarket BTC Monitor

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/work.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test your changes
6. Commit and push
7. Create a Pull Request

## 📋 Development Setup

### Prerequisites

- Python 3.12+
- Git
- pip

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio black flake8
```

## 🧪 Testing

### Run all tests
```bash
pytest tests/ -v
```

### Run with coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

### Test a specific module
```bash
pytest tests/test_market_discovery.py -v
```

## 📝 Code Style

We follow PEP 8 style guidelines. Use these tools:

### Format code
```bash
black src/ tests/
```

### Lint code
```bash
flake8 src/ tests/
```

### Type checking (optional)
```bash
mypy src/
```

## 🏗️ Project Structure

When adding new features, follow this structure:

- `src/core/` - Core functionality (market discovery, websocket)
- `src/alerts/` - Alert and notification systems
- `src/ui/` - User interface components
- `src/utils/` - Utility functions and helpers
- `tests/` - Test files (mirror src/ structure)

## 📦 Adding Dependencies

1. Add to `requirements.txt`
2. Document why it's needed
3. Update README if user-facing

## 🐛 Reporting Bugs

### Before reporting

- Check existing issues
- Verify it's reproducible
- Test with latest version

### Bug report should include

- Python version
- Operating system
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error messages/logs
- Screenshots (if applicable)

## ✨ Feature Requests

### Good feature requests include

- Clear use case
- Expected behavior
- Alternative solutions considered
- Willingness to implement

## 📬 Pull Request Process

1. **Update documentation** - README, docstrings, etc.
2. **Add tests** - All new code should have tests
3. **Follow style guide** - Run black and flake8
4. **Write clear commits** - Descriptive commit messages
5. **Update CHANGELOG** - Document your changes
6. **Request review** - Tag maintainers

### PR Title Format

Use conventional commits:

- `feat: Add new feature`
- `fix: Fix bug in market discovery`
- `docs: Update README`
- `test: Add tests for alerts`
- `refactor: Improve websocket handling`
- `chore: Update dependencies`

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows style guide
- [ ] All tests pass
```

## 🎯 Priority Areas

We're especially interested in contributions for:

1. **Historical Data Storage** - SQLite/Redis integration
2. **Web Dashboard** - Flask/FastAPI web interface
3. **Advanced Analytics** - Moving averages, pattern detection
4. **Notification Channels** - Email, Slack, etc.
5. **Performance Optimization** - Faster data processing
6. **Documentation** - Tutorials, examples
7. **Tests** - Increase coverage

## 🤔 Questions?

- Open a GitHub Discussion
- Check existing issues
- Read the documentation

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You!

Every contribution, no matter how small, is valuable and appreciated!
