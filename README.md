# Bitwarden CLI Vault Management API

This module supports the [Bitwarden CLI Vault Management
API](https://bitwarden.com/help/vault-management-api/), available via
Bitwarden CLI's `bw serve` command.

If you're looking for Bitwarden's public api (for organizational tools and
stuff) that API is [available here](https://bitwarden.com/help/api/).

This library focuses on providing a clean Python interface to the Bitwarden
Vault Management API. It does not handle authentication or login processes -
users must manage their own Bitwarden CLI authentication and provide the
necessary session keys to the library.

## Generated Code

The data models in `bw_serve_client/models.py` are generated, as pydantic 2
models, from Bitwarden's published OpenAPI spec for the Vault Management API.
The resource classes that call the API, such as `bw_serve_client/folders.py`,
are written by hand.

Bitwarden publishes the spec only inside its [Vault Management API help
page][vm-api]. There is no standalone JSON file, and the spec's own version
is always `latest`. A copy of it is committed in `upstream/`, along with the
local fixes the generator needs and the patched spec they produce.

`pipeline.py` keeps it current in three stages: `detect` reports whether
Bitwarden changed anything, `build` patches the spec and regenerates the
models, and `check` runs the tests. `update` runs all three. Running them on
a schedule is planned on the [project board][project].

```bash
poetry run python pipeline.py update   # or detect, build, check
```

Each stage exits 0 when nothing changed, 1 on an error, and 2 when something
changed and there is work to do. `make detect`, `make build`, `make check`
and `make update` run the same stages, but make exits 2 for every failure, so
call `pipeline.py` directly when the exit code matters.

| Path | What it holds |
|------|---------------|
| `pipeline.py` | The update pipeline's entry point. |
| `upstream/` | The committed Bitwarden spec and the other upstream snapshots, the lock file, the local fixes, the patched spec, and the detection and spec tools. See `upstream/README.md`. |
| `codegen/` | Inputs to model generation. See `codegen/README.md`. |

[vm-api]: https://bitwarden.com/help/vault-management-api/
[project]: https://github.com/users/harleypig/projects/3

## Requirements

* Python 3.10+

* [Bitwarden
    CLI](https://bitwarden.com/download/#downloads-command-line-interface)
  - Instructions can be found
    [in the official documentation](https://bitwarden.com/help/cli/#download-and-install)

## Prerequisites

### Bitwarden CLI Setup

This library requires the [Bitwarden CLI](https://bitwarden.com/download/#downloads-command-line-interface)
to be installed and configured. The CLI must be authenticated and the vault
unlocked before using this library.

#### Bitwarden CLI Installation

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
