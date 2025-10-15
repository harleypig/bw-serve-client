# Bitwarden CLI Vault Management API

This module supports the [Bitwarden CLI Vault Management
API](https://bitwarden.com/help/vault-management-api/), available via
Bitwarden CLI's `bw serve` command.

If you're looking for Bitwarden's public api (for organizational tools and
stuff) that API is [here](https://bitwarden.com/help/api/).

This library focuses on providing a clean Python interface to the Bitwarden
Vault Management API. It does not handle authentication or login processes -
users must manage their own Bitwarden CLI authentication and provide the
necessary session keys to the library.

## Generated Code

This library is generated from the Bitwarden Vault Management API swagger
specification. The source swagger file is located at
`docs/vault-management-api.json`.

### Utility Scripts

Development and maintenance utilities are located in the `scripts/` directory:

- **`scripts/extract_routes.py`** - Extract API routes from the swagger file for documentation
- See `scripts/README.md` for detailed usage instructions

You can also use the provided Makefile for common tasks:

```bash
make extract-routes      # Extract routes in markdown format
make extract-routes-text # Extract routes in text format
make extract-routes-json # Extract routes in JSON format
make help               # Show all available commands
```

## Requirements

* Python 3.10+

* [Bitwarden
    CLI](https://bitwarden.com/download/#downloads-command-line-interface)
  - Instructions can be found
    [here](https://bitwarden.com/help/cli/#download-and-install)

## Prerequisites

### Bitwarden CLI Setup

This library requires the [Bitwarden CLI](https://bitwarden.com/download/#downloads-command-line-interface)
to be installed and configured. The CLI must be authenticated and the vault
unlocked before using this library.

#### Installation

Follow the [official installation guide](https://bitwarden.com/help/cli/#download-and-install)
for your operating system.

#### Authentication

The Bitwarden CLI must be authenticated before using this library. This
typically involves:

1. **Login** (one-time setup):
   ```bash
   bw login
   # or with API key:
   bw login --apikey
   ```

2. **Unlock** (required each session):
   ```bash
   bw unlock
   # or with environment variable:
   bw unlock --passwordenv BW_PASSWORD
   # or with password file:
   bw unlock --passwordfile /path/to/password.txt
   ```

3. **Start the API server**:
   ```bash
   bw serve
   # or with custom port:
   bw serve --port 8080
   ```

#### Session Key

After unlocking, the CLI returns a session key that must be provided to this
library for API authentication. You can capture it like this:

```bash
# Get session key only (raw output)
BW_SESSION="$(bw unlock --raw)"

# Or check if already unlocked
bw status
```

The session key is then passed to the library's client constructor.

### Library Authentication

This library does **not** handle Bitwarden CLI authentication or login
processes. It expects:

1. The `bw serve` server to be running and accessible
2. A valid session key to be provided for API authentication
3. The vault to be unlocked (session key valid)

The library focuses on providing a clean Python interface to the API endpoints
once authentication is handled externally.

## Installation

### pip install

If the python package is hosted on a repository, you can install directly using:

```sh
pip install git+https://github.com/harleypig/bw-serve-client.git
```

(you may need to run `pip` with root permission: `sudo pip install
git+https://github.com/harleypig/bw-serve-client.git`)

Then import the package:

```python
import bw_serve_client
```

### Tests

Execute `pytest` to run the tests.

## Getting Started

### Basic Usage

```python
import bw_serve_client

# Initialize client with session key
client = bw_serve_client.Client(
    base_url="http://localhost:8087",  # Default bw serve URL
    session_key="your_session_key_here"
)

# List vault items
items = client.list_items()

# Get a specific item
item = client.get_item("item-id-here")

# Create a new folder
folder = client.create_folder({"name": "My New Folder"})
```

### Session Key Management

The library requires a valid session key for all API operations. You can
obtain this from the Bitwarden CLI:

```python
import subprocess
import bw_serve_client

# Get session key from CLI
result = subprocess.run(
    ["bw", "unlock", "--raw"], 
    capture_output=True, 
    text=True
)
session_key = result.stdout.strip()

# Initialize client
client = bw_serve_client.Client(session_key=session_key)
```

**Note**: Session keys expire when the vault is locked or after a period of
inactivity. You may need to refresh the session key periodically.

## Documentation for API Endpoints

XXX: TBD

## Documentation For Models

XXX: TBD
