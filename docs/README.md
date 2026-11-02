# Documentation

The written docs for `bw-serve-client`, a Python client for the HTTP API
that the Bitwarden CLI's `bw serve` provides. The API reference, generated
from the docstrings, is published at
[harleypig.github.io/bw-serve-client][pages].

## Using the library

- [When to use it][when] — whether this library fits what you are building.
- [Installation][install] — the package from git, and a running `bw serve`.
- [Quick start][quick] — reading and writing the vault, and handling
  errors.
- [Examples][examples] — one runnable script per resource class.
- [API architecture][arch] — every resource class, its methods and the
  routes they call.

## Working on the library

- [Development setup][dev] — install, test, lint and build the docs.
- [Contributing][contrib] — issues, pull requests and releases.
- [Update pipeline][pipeline] — how `pipeline.py` detects upstream
  changes and regenerates the models.

## Bitwarden

- [Bitwarden CLI][cli] — installing `bw`, logging in, and `bw serve`.
- [Vault Management API][vm-api] — Bitwarden's reference for the routes
  `bw serve` exposes.

[arch]: api-architecture.md
[cli]: https://bitwarden.com/help/cli/
[contrib]: developer/contributing.md
[dev]: development.md
[examples]: https://github.com/harleypig/bw-serve-client/tree/master/examples
[install]: user/installation.md
[pipeline]: developer/update-pipeline.md
[pages]: https://harleypig.github.io/bw-serve-client/
[quick]: user/quick-start.md
[vm-api]: https://bitwarden.com/help/vault-management-api/
[when]: when-to-use.md
