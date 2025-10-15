# Bitwarden CLI Vault Management API

This module supports the [Bitwarden CLI Vault Management
API](https://bitwarden.com/help/vault-management-api/), available via
Bitwarden CLI's `bw serve` command.

If you're looking for Bitwarden's public api (for organizational tools and
stuff) that API is [here](https://bitwarden.com/help/api/).

Please note that this module won't be supporting email and master password
login to start with. It's not the most secure method, but pull requests are
welcome. Also, SSO support is low on the todo list, as the author doesn't use
it.

## Generated Code

This library is generated from the Bitwarden Vault Management API swagger specification. The source swagger file is located at `docs/vault-management-api.json`.

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

## `bw serve` Configuration

This module expects the user of this module to manage the configuration and
setup of the `bw serve` server. Documentation is
[here](https://bitwarden.com/help/cli/#serve).

### Authentication Steps

These authentication steps are required for the `bw` cli tool regardless of
how it's being used. I'm including the basic steps you'll need to use this
module here for completeness. Be sure to read the
[documentation](https://bitwarden.com/help/cli/).

* Check status
  - unauthenticated, need to run `bw login --apikey`
  - locked, need to run `bw unlock`
  - unlocked, nothing needs to be done

#### `bw login --apikey`

* [docs](https://bitwarden.com/help/cli/#using-an-api-key)

Environment variables (both required):

* BW_CLIENTID
* BW_CLIENTSECRET

#### `bw unlock`

[docs](https://bitwarden.com/help/cli/#unlock)

* --passwordenv <ENVIRONMENT_VARIABLE>
* --passwordfile /path/to/file
* prompt for password

Capture BW_SESSION and set it.

In bash, only bash scripts can be sourced, so we can't set the environment
variable outside of the script. Provide an option for the user to be to do
something like the following.

```
BW_SESSION="$(bw-serve-client unlock [--passwordenv|--passwordfile|prompt])"
```

So they aren't stomping all over themselves when using both the command line
and this module.

There is a --session option for each command, but I'm not supporting that.

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

XXX: TBD

## Documentation for API Endpoints

XXX: TBD

## Documentation For Models

XXX: TBD
