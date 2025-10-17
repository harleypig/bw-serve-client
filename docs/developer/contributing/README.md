# Contributing to bw-serve-client

Thank you for your interest in contributing to `bw-serve-client`! This guide will help you contribute effectively to the project.

## 🤝 How to Contribute

### Types of Contributions

We welcome several types of contributions:

- **🐛 Bug Reports** - Report issues and bugs
- **✨ Feature Requests** - Suggest new features
- **📝 Documentation** - Improve documentation
- **🧪 Tests** - Add or improve tests
- **🔧 Code** - Fix bugs or implement features
- **🎨 Code Quality** - Improve code style and performance

### Getting Started

1. **Fork the Repository**

   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/your-username/bw-serve-client.git
   cd bw-serve-client
   ```

2. **Set Up Development Environment**
   - Follow the [Development Setup Guide](../setup/development-environment.md)
   - Install dependencies: `poetry install`
   - Install pre-commit hooks: `poetry run pre-commit install`

3. **Create a Feature Branch**

   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b bugfix/issue-description
   ```

## 📋 Contribution Process

### 1. Before You Start

- **Check existing issues** - Avoid duplicate work
- **Discuss major changes** - Open an issue for discussion
- **Read the codebase** - Understand the architecture
- **Review guidelines** - Follow coding standards

### 2. Making Changes

#### Code Changes

- Follow the [Code Style Guide](code-style.md)
- Write comprehensive tests
- Update documentation
- Ensure all tests pass

#### Documentation Changes

- Use clear, concise language
- Follow the [Documentation Style Guide](documentation-style.md)
- Include examples where helpful
- Update related documentation

#### Test Changes

- Follow the [Testing Guide](../testing/README.md)
- Maintain or improve test coverage
- Add tests for new functionality
- Update existing tests if needed

### 3. Testing Your Changes

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=bw_serve_client

# Run code quality checks
poetry run pre-commit run --all-files

# Run type checking
poetry run mypy bw_serve_client/
poetry run pyright bw_serve_client/
```

### 4. Submitting Changes

#### Commit Messages

Use conventional commit format:

```bash
# Format: type(scope): description
git commit -m "feat(api): add new endpoint support"
git commit -m "fix(client): resolve connection timeout issue"
git commit -m "docs(readme): update installation instructions"
git commit -m "test(api): add tests for error handling"
```

**Types:**

- `feat` - New features
- `fix` - Bug fixes
- `docs` - Documentation changes
- `style` - Code style changes
- `refactor` - Code refactoring
- `test` - Test changes
- `chore` - Maintenance tasks

#### Pull Request Process

1. **Push your changes**

   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request**
   - Use the [PR template](.github/pull_request_template.md)
   - Provide clear description
   - Link related issues
   - Include screenshots for UI changes

3. **Respond to feedback**
   - Address review comments
   - Make requested changes
   - Update documentation if needed

## 📏 Code Standards

### Python Code Style

- **PEP 8** compliance
- **Type hints** for all public methods
- **Docstrings** in Google style
- **Line length** of 88 characters (Black standard)

### Code Quality Tools

- **yapf** - Code formatting
- **flake8** - Linting
- **mypy** - Type checking
- **pyright** - Advanced type checking
- **pydocstyle** - Docstring style
- **bandit** - Security linting
- **isort** - Import sorting

### Example Code Style

```python
from typing import Optional, Dict, Any
import logging

class ApiClient:
    """Client for Bitwarden Vault Management API.

    This class provides methods for interacting with the Bitwarden
    Vault Management API, including authentication, data retrieval,
    and error handling.

    Args:
        protocol: Protocol to use (http, https)
        domain: Domain or IP address
        port: Port number
        timeout: Request timeout in seconds
        logger: Optional logger instance
    """

    def __init__(
        self,
        protocol: str = "http",
        domain: str = "localhost",
        port: int = 8087,
        timeout: int = 30,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """Initialize the API client."""
        self.protocol = protocol
        self.domain = domain
        self.port = port
        self.timeout = timeout
        self.logger = logger or self._setup_default_logger()

    def get(self, endpoint: str, **kwargs) -> Any:
        """Make a GET request to the API.

        Args:
            endpoint: API endpoint path
            **kwargs: Additional arguments for requests

        Returns:
            Response data

        Raises:
            BitwardenAPIError: For API errors
        """
        return self._make_request("GET", endpoint, **kwargs)
```

## 🧪 Testing Standards

### Test Requirements

- **Unit tests** for all public methods
- **Integration tests** for API interactions
- **Error handling tests** for exception cases
- **Edge case tests** for boundary conditions
- **Mock external dependencies** appropriately

### Test Structure

```python
import pytest
from unittest.mock import Mock, patch
from bw_serve_client import ApiClient, BitwardenAPIError

class TestApiClient:
    """Test cases for ApiClient class."""

    def test_init_default_values(self):
        """Test ApiClient initialization with default values."""
        client = ApiClient()
        assert client.protocol == "http"
        assert client.domain == "localhost"
        assert client.port == 8087

    def test_get_request_success(self):
        """Test successful GET request."""
        with patch('bw_serve_client.api_client.requests.Session') as mock_session:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            mock_session.return_value.request.return_value = mock_response

            client = ApiClient()
            result = client.get("/test")

            assert result == {"success": True}

    def test_get_request_error(self):
        """Test GET request with error response."""
        with patch('bw_serve_client.api_client.requests.Session') as mock_session:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"error": "Not found"}
            mock_session.return_value.request.return_value = mock_response

            client = ApiClient()

            with pytest.raises(BitwardenAPIError):
                client.get("/test")
```

## 📝 Documentation Standards

### Docstring Format

Use Google-style docstrings:

```python
def method_name(self, param1: str, param2: int = 10) -> bool:
    """Brief description of the method.

    Longer description if needed, explaining the purpose,
    behavior, and any important details about the method.

    Args:
        param1: Description of param1
        param2: Description of param2 (default: 10)

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is invalid
        BitwardenAPIError: When API request fails

    Example:
        >>> client = ApiClient()
        >>> result = client.method_name("test", 20)
        >>> print(result)
        True
    """
```

### README Updates

When adding features, update relevant documentation:

- **Installation instructions** if dependencies change
- **Usage examples** for new features
- **Configuration options** for new settings
- **API reference** for new methods

## 🐛 Bug Reports

### Before Reporting

1. **Check existing issues** - Search for similar reports
2. **Test latest version** - Ensure bug exists in current code
3. **Gather information** - Collect relevant details

### Bug Report Template

```markdown
## Bug Description
Brief description of the bug

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- Python version: 3.12.3
- Library version: 0.1.0
- OS: Linux/macOS/Windows
- Bitwarden server version: X.X.X

## Additional Context
Any other relevant information
```

## ✨ Feature Requests

### Before Requesting

1. **Check existing features** - Ensure feature doesn't exist
2. **Search issues** - Look for similar requests
3. **Consider alternatives** - Is there a workaround?

### Feature Request Template

```markdown
## Feature Description
Brief description of the feature

## Use Case
Why is this feature needed?

## Proposed Solution
How should this feature work?

## Alternatives Considered
What other approaches were considered?

## Additional Context
Any other relevant information
```

## 🔍 Code Review Process

### Review Checklist

- [ ] **Code follows style guidelines**
- [ ] **Tests are comprehensive and pass**
- [ ] **Documentation is updated**
- [ ] **No breaking changes without discussion**
- [ ] **Performance impact is considered**
- [ ] **Security implications are reviewed**

### Review Guidelines

- **Be constructive** - Provide helpful feedback
- **Be specific** - Point out exact issues
- [ ] **Be respectful** - Maintain professional tone
- [ ] **Be thorough** - Check all aspects of the code

## 🏷️ Release Process

### Version Numbering

We use [Semantic Versioning](https://semver.org/):

- **MAJOR** - Breaking changes
- **MINOR** - New features (backward compatible)
- **PATCH** - Bug fixes (backward compatible)

### Release Checklist

- [ ] **All tests pass**
- [ ] **Documentation is updated**
- [ ] **Version number is bumped**
- [ ] **CHANGELOG is updated**
- [ ] **Release notes are prepared**

## 🆘 Getting Help

### Resources

- **[Development Setup](../setup/development-environment.md)** - Environment setup
- **[Testing Guide](../testing/README.md)** - Testing best practices
- **[Code Style Guide](code-style.md)** - Coding standards
- **[Architecture Guide](../architecture/overview.md)** - Codebase structure

### Community

- **GitHub Issues** - Bug reports and feature requests
- **GitHub Discussions** - Questions and general discussion
- **Pull Requests** - Code contributions

## 📜 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors.

### Expected Behavior

- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Accept constructive criticism gracefully
- Focus on what's best for the community

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or inflammatory comments
- Personal attacks or political discussions
- Spam or off-topic discussions

## 🎉 Recognition

Contributors will be recognized in:

- **CONTRIBUTORS.md** - List of all contributors
- **Release notes** - Major contributors highlighted
- **GitHub** - Contributor statistics and badges

---

*Ready to contribute? Start with the [Development Setup Guide](../setup/development-environment.md) and then check out our [open issues](https://github.com/harleypig/bw-serve-client/issues)!*
