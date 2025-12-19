# Contributing to E-Commerce Voice Bot

First off, thank you for considering contributing to E-Commerce Voice Bot! 🎉

## 🤝 How Can I Contribute?

### Reporting Bugs 🐛

Before creating bug reports, please check existing issues to avoid duplicates.

When creating a bug report, include:
- **Clear title and description**
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Screenshots** (if applicable)
- **Environment details** (OS, Python version, etc.)

### Suggesting Features ✨

Feature requests are welcome! Please include:
- **Clear use case**
- **Why this feature would be useful**
- **Possible implementation approach**

### Pull Requests 🔄

1. **Fork the repository**
2. **Create a new branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Write/update tests** (if applicable)
5. **Update documentation**
6. **Commit with clear messages**
   ```bash
   git commit -m "Add: feature description"
   ```
7. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```
8. **Open a Pull Request**

## 📝 Code Style

### Python
- Follow **PEP 8** style guide
- Use **type hints** where possible
- Keep functions **small and focused**
- Add **docstrings** for classes and functions

Example:
```python
def search_products(query: str, limit: int = 10) -> List[Dict]:
    """
    Search for products using semantic search.
    
    Args:
        query: Search query from user
        limit: Maximum number of results
        
    Returns:
        List of product dictionaries
    """
    # Implementation here
    pass
```

### Formatting
We use **Black** for code formatting:
```bash
black app/
```

## 🧪 Testing

Before submitting a PR, ensure:
- [ ] All existing tests pass
- [ ] New features have tests
- [ ] Code is formatted with Black
- [ ] No linting errors

```bash
# Run tests
pytest

# Format code
black app/

# Check linting
flake8 app/
```

## 📚 Documentation

- Update README.md if adding new features
- Update PROJECT_DOCUMENTATION.md for architectural changes
- Add docstrings to new functions/classes
- Update API endpoint documentation

## 🌳 Git Commit Messages

Use clear, descriptive commit messages:

- **Add**: New feature or functionality
- **Fix**: Bug fix
- **Update**: Changes to existing features
- **Refactor**: Code restructuring
- **Docs**: Documentation changes
- **Test**: Adding or updating tests
- **Style**: Code formatting changes

Examples:
```
Add: Product recommendation feature
Fix: Order tracking regex pattern
Update: LLM response formatting
Docs: Add API usage examples
```

## 🏗️ Project Structure

Please maintain the existing structure:
```
app/
├── service/        # Business logic
├── config/         # Configuration
├── core/           # Core settings
└── server.py       # FastAPI routes
```

## 🔐 Security

- **Never commit API keys** or sensitive data
- Use environment variables for secrets
- Follow security best practices
- Report security vulnerabilities privately

## 📧 Questions?

Feel free to:
- Open a [Discussion](https://github.com/SRIRAMCHINMAY/Ecommerce-VoiceBot/discussions)
- Ask in [Issues](https://github.com/SRIRAMCHINMAY/Ecommerce-VoiceBot/issues)
- Email: sriramchinmay@gmail.com

## ⭐ Recognition

Contributors will be:
- Listed in the project's README
- Mentioned in release notes
- Given credit in documentation

Thank you for contributing! 🙏

