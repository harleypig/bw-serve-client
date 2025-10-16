# Installation Guide

This guide will help you install and set up the `bw-serve-client` library.

## 📋 Prerequisites

Before installing `bw-serve-client`, ensure you have:

- **Python 3.9+** (3.12 recommended)
- **pip** or **Poetry** package manager
- **Bitwarden Server** running with Vault Management API enabled
- **Authentication token** for your Bitwarden server

## 🚀 Installation Methods

### Method 1: Using pip (Recommended)

```bash
# Install from PyPI (when available)
pip install bw-serve-client

# Or install from GitHub
pip install git+https://github.com/harleypig/bw-serve-client.git
```

### Method 2: Using Poetry

```bash
# Add to your project
poetry add bw-serve-client

# Or add from GitHub
poetry add git+https://github.com/harleypig/bw-serve-client.git
```

### Method 3: Development Installation

```bash
# Clone the repository
git clone https://github.com/harleypig/bw-serve-client.git
cd bw-serve-client

# Install in development mode
pip install -e .

# Or with Poetry
poetry install
```

## 🔧 Configuration

### Environment Variables

Set up your environment variables for easy configuration:

```bash
# Required: Bitwarden server URL
export BW_SERVE_URL="https://your-bitwarden-server.com"

# Required: Authentication token
export BW_SERVE_TOKEN="your-auth-token"

# Optional: Request timeout (default: 30 seconds)
export BW_SERVE_TIMEOUT="30"
```

### Configuration File

Create a configuration file for persistent settings:

```json
{
  "server": {
    "protocol": "https",
    "domain": "your-bitwarden-server.com",
    "port": 443,
    "path": ""
  },
  "auth": {
    "token": "your-auth-token"
  },
  "timeout": 30,
  "max_retries": 3
}
```

## ✅ Verification

Test your installation with a simple connection test:

```python
from bw_serve_client import ApiClient

# Create client instance
client = ApiClient(
    protocol="https",
    domain="your-bitwarden-server.com",
    port=443
)

# Test connection (this will make a simple API call)
try:
    response = client.get("/health")
    print("✅ Connection successful!")
    print(f"Response: {response}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

## 🔍 Troubleshooting

### Common Installation Issues

#### Python Version Compatibility
```bash
# Check your Python version
python --version

# Should be 3.9 or higher
```

#### Permission Issues
```bash
# Install with user flag if you get permission errors
pip install --user bw-serve-client

# Or use a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install bw-serve-client
```

#### Network Issues
```bash
# If you're behind a corporate firewall
pip install --trusted-host pypi.org --trusted-host pypi.python.org bw-serve-client
```

### Verification Issues

#### Connection Refused
- Check that your Bitwarden server is running
- Verify the URL and port are correct
- Ensure the Vault Management API is enabled

#### Authentication Failed
- Verify your authentication token is valid
- Check token permissions and expiration
- Ensure the token has the necessary scopes

#### SSL/TLS Issues
```python
# For self-signed certificates, you may need to disable SSL verification
# (NOT recommended for production)
import ssl
import requests

# Disable SSL verification (development only)
requests.packages.urllib3.disable_warnings()
```

## 📚 Next Steps

After successful installation:

1. **[Quick Start Guide](../tutorials/quick-start.md)** - Get up and running quickly
2. **[Authentication Setup](authentication.md)** - Configure authentication properly
3. **[API Reference](../api-reference/)** - Explore the full API

## 🆘 Getting Help

If you encounter issues:

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Review [Common Issues](common-issues.md)
3. Search [existing issues](https://github.com/harleypig/bw-serve-client/issues)
4. [Open a new issue](https://github.com/harleypig/bw-serve-client/issues/new)

---

*Installation complete? Head to the [Quick Start Tutorial](../tutorials/quick-start.md) to begin using the library!*