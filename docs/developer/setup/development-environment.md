# Development Environment Setup

This guide will help you set up a complete development environment for contributing to `bw-serve-client`.

## 📋 Prerequisites

Before setting up your development environment, ensure you have:

- **Python 3.9+** (3.12 recommended)
- **Git** for version control
- **Poetry** for dependency management
- **VS Code** or **PyCharm** (recommended IDEs)
- **Docker** (optional, for testing with Bitwarden server)

## 🚀 Quick Setup

### 1. Clone the Repository

```bash
git clone https://github.com/harleypig/bw-serve-client.git
cd bw-serve-client
```

### 2. Install Dependencies

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Activate the virtual environment
poetry shell
```

### 3. Install Pre-commit Hooks

```bash
# Install pre-commit hooks
poetry run pre-commit install

# Install fix hooks (optional)
poetry run pre-commit install --hook-type pre-commit --config .pre-commit-config-fix.yaml
```

### 4. Verify Installation

```bash
# Run tests to verify everything works
poetry run pytest

# Run code quality checks
poetry run pre-commit run --all-files
```

## 🛠️ Detailed Setup

### Python Environment

#### Using Poetry (Recommended)

```bash
# Create virtual environment
poetry install --with dev

# Activate environment
poetry shell

# Verify Python version
python --version  # Should be 3.9+
```

#### Using venv (Alternative)

```bash
# Create virtual environment
python -m venv venv

# Activate environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### IDE Configuration

#### VS Code Setup

1. **Install Extensions:**
   ```json
   {
     "recommendations": [
       "ms-python.python",
       "ms-python.pylint",
       "ms-python.flake8",
       "ms-python.mypy",
       "ms-python.black-formatter",
       "ms-python.isort",
       "ms-toolsai.jupyter"
     ]
   }
   ```

2. **Configure Settings:**
   ```json
   {
     "python.defaultInterpreterPath": "./venv/bin/python",
     "python.linting.enabled": true,
     "python.linting.pylintEnabled": true,
     "python.linting.flake8Enabled": true,
     "python.linting.mypyEnabled": true,
     "python.formatting.provider": "black",
     "python.sortImports.args": ["--profile", "black"],
     "editor.formatOnSave": true,
     "editor.codeActionsOnSave": {
       "source.organizeImports": true
     }
   }
   ```

#### PyCharm Setup

1. **Open Project:**
   - File → Open → Select project directory
   - Configure Python interpreter to use Poetry environment

2. **Configure Code Style:**
   - Settings → Editor → Code Style → Python
   - Set line length to 88 (Black standard)
   - Configure import sorting

3. **Enable Inspections:**
   - Settings → Editor → Inspections
   - Enable Python → PEP 8, PyLint, MyPy

### Development Tools

#### Pre-commit Configuration

The project uses pre-commit hooks for code quality:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: yapf
        name: yapf
        entry: poetry run yapf
        language: system
        types: [python]
      - id: flake8
        name: flake8
        entry: poetry run flake8
        language: system
        types: [python]
      - id: mypy
        name: mypy
        entry: poetry run mypy
        language: system
        types: [python]
```

#### Testing Configuration

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=bw_serve_client

# Run specific test file
poetry run pytest tests/test_api_client.py

# Run with verbose output
poetry run pytest -v
```

## 🐳 Docker Setup (Optional)

For testing with a real Bitwarden server:

### 1. Start Bitwarden Server

```bash
# Using Docker Compose
docker-compose up -d bitwarden

# Or using Docker directly
docker run -d \
  --name bitwarden \
  -p 8087:8087 \
  -e BW_SERVE_TOKEN=your-token \
  bitwarden/bitwarden:latest
```

### 2. Test Connection

```python
from bw_serve_client import ApiClient

client = ApiClient(protocol="http", domain="localhost", port=8087)
response = client.get("/health")
print(response)
```

## 🔧 Configuration Files

### Poetry Configuration

```toml
# pyproject.toml
[tool.poetry]
name = "bw-serve-client"
version = "0.1.0"
description = "Python client for Bitwarden Vault Management API"

[tool.poetry.dependencies]
python = "^3.9"
requests = "^2.31.0"
urllib3 = "^2.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-cov = "^4.1.0"
pytest-mock = "^3.11.0"
yapf = "^0.40.0"
flake8 = "^6.0.0"
mypy = "^1.5.0"
pyright = "^1.1.0"
pydocstyle = "^6.3.0"
bandit = "^1.7.0"
isort = "^5.12.0"
pre-commit = "^3.4.0"
```

### VS Code Workspace

```json
{
  "folders": [
    {
      "path": "."
    }
  ],
  "settings": {
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },
  "extensions": {
    "recommendations": [
      "ms-python.python",
      "ms-python.pylint",
      "ms-python.flake8",
      "ms-python.mypy",
      "ms-python.black-formatter",
      "ms-python.isort"
    ]
  }
}
```

## ✅ Verification

### 1. Run All Tests

```bash
poetry run pytest tests/ -v
```

Expected output:
```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-8.4.2
collected 56 items

tests/test_api_client.py::TestApiClient::test_init_default_values PASSED
tests/test_api_client.py::TestApiClient::test_init_custom_values PASSED
...
============================== 56 passed in 0.38s ==============================
```

### 2. Run Code Quality Checks

```bash
poetry run pre-commit run --all-files
```

Expected output:
```
check yaml...............................................................Passed
check json...............................................................Passed
yapf.....................................................................Passed
isort....................................................................Passed
flake8...................................................................Passed
mypy.....................................................................Passed
pyright..................................................................Passed
pydocstyle...............................................................Passed
bandit...................................................................Passed
```

### 3. Check Type Safety

```bash
poetry run mypy bw_serve_client/
poetry run pyright bw_serve_client/
```

## 🚀 Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write code following the [Code Style Guide](../contributing/code-style.md)
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run tests
poetry run pytest

# Run code quality checks
poetry run pre-commit run --all-files

# Run type checking
poetry run mypy bw_serve_client/
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add new feature"
```

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
# Create pull request on GitHub
```

## 🆘 Troubleshooting

### Common Issues

#### Poetry Installation Issues

```bash
# Update Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Clear Poetry cache
poetry cache clear --all pypi
```

#### Pre-commit Hook Issues

```bash
# Update pre-commit hooks
poetry run pre-commit autoupdate

# Skip hooks temporarily
git commit --no-verify -m "commit message"
```

#### Test Failures

```bash
# Run tests with verbose output
poetry run pytest -v -s

# Run specific test
poetry run pytest tests/test_api_client.py::TestApiClient::test_specific_method -v
```

#### Import Issues

```bash
# Reinstall package in development mode
poetry run pip install -e .

# Check Python path
poetry run python -c "import sys; print(sys.path)"
```

## 📚 Next Steps

After setting up your development environment:

1. **[Read the Architecture Guide](../architecture/overview.md)** - Understand the codebase
2. **[Review Contributing Guidelines](../contributing/README.md)** - Learn how to contribute
3. **[Check the Testing Guide](../testing/README.md)** - Learn testing best practices
4. **[Start Contributing](../contributing/pull-requests.md)** - Make your first contribution

---

*Environment setup complete? Check out the [Architecture Overview](../architecture/overview.md) to understand the codebase!*