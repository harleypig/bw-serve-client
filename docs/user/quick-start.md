# Quick Start

From an installed package to reading your vault in Python. Every snippet on
this page needs a running `bw serve` with the vault unlocked, on
`localhost:8087`; [Installation][install] covers both the package and the
server.

## Read the vault

```python
from bw_serve_client import ApiClient
from bw_serve_client import Folders
from bw_serve_client import VaultItems

with ApiClient(base_url="http://localhost:8087") as client:
  for folder in Folders(client).list():
    print(folder.name)

  for item in VaultItems(client).list(search="example.com"):
    print(item.name)
```

`ApiClient` holds the connection; use it as a context manager so it closes.
Each group of routes is a resource class built on the client, as
`Folders(client)` is here. It sends no token or session key: the vault is
unlocked inside `bw serve`, not in your program.

Results come back as pydantic models, the same ones the package exports
(`FolderSchema`, `ItemSchema` and the rest). Secret fields such as
`item.login.password` are `SecretStr`, which prints as asterisks; call
`get_secret_value()` when you need the value itself.

## Write, then sync

```python
from bw_serve_client import ApiClient
from bw_serve_client import Folders
from bw_serve_client import VaultControl

with ApiClient(base_url="http://localhost:8087") as client:
  folders = Folders(client)
  folder = folders.add("Example folder")
  VaultControl(client).sync()
  print(len(folders.list()), "folders, including", folder.name)
```

`bw serve` can answer a read with data from before your last write. Call
`VaultControl(client).sync()` between writing something and reading it back.

## Handle errors

By default every failure raises, and every error is a `BitwardenError`. The
subclass says whose problem it is:

| Error | Raised when |
|-------|-------------|
| `UserError` | The vault is locked or no one is logged in. |
| `ValidationError` | The request is wrong: a bad argument, or an id that names nothing. |
| `ExternalServiceError` | `bw serve` is unreachable, times out, fails, or answers with something unparseable. |
| `InternalError` | A bug in this library. |

```python
from bw_serve_client import ApiClient
from bw_serve_client import ExternalServiceError
from bw_serve_client import Folders
from bw_serve_client import UserError

with ApiClient(base_url="http://localhost:8087") as client:
  try:
    folders = Folders(client).list()

  except UserError:
    print("Unlock the vault first")

  except ExternalServiceError as error:
    print(f"bw serve failed: {error}")
```

To have validation and user errors returned instead of raised, pass
`error_handler=DefaultErrorHandler(error_level=logging.ERROR)` to
`ApiClient`; service failures and bugs still raise. Any object that
implements the `ErrorHandler` protocol can replace the default, and a
`logger` argument replaces the default logger.

## Connect another way

- **Another host or port:** pass it in `base_url`, such as
  `ApiClient(base_url="http://localhost:9000")` for `bw serve --port 9000`.
- **A Unix socket:** start `bw serve --hostname unix:///path/to/bw.sock` and
  pass `base_url="unix:///path/to/bw.sock"`. If `bw serve` also had
  `--port`, pass the same `port=` to `ApiClient`, which sends it in the
  `Host` header. [`examples/serve_socket.py`][ex-socket] starts a server on
  a socket and queries it.
- **Your own transport:** pass any `httpx` transport as `transport=`.

## Next

There is one resource class per group of routes, and one runnable example
for each in [`examples/`][examples]:

| Class | Covers | Example |
|-------|--------|---------|
| `Folders` | Folders | [`folders.py`][ex-folders] |
| `VaultItems` | Items: add, find, edit, archive, trash, restore | [`vault_items.py`][ex-vault-items] |
| `ItemFields` | One field of an item: username, password, URI, TOTP, notes, breach check | [`item_fields.py`][ex-item-fields] |
| `Attachments` | Item attachments | [`attachments.py`][ex-attachments] |
| `Sends` | Bitwarden Send | [`sends.py`][ex-sends] |
| `VaultControl` | Status, sync, lock and unlock | [`vault_control.py`][ex-vault-control] |
| `Utilities` | Templates, the account fingerprint, password generation | [`utilities.py`][ex-utilities] |
| `Organizations` | Organizations, listing and confirming members | [`organizations.py`][ex-organizations] |
| `OrgCollections` | Collections, moving an item into an organization | [`org_collections.py`][ex-org-collections] |
| `DeviceApproval` | Device approval requests | [`device_approval.py`][ex-device-approval] |

Each example's docstring says what it needs and how to run it. Every method
and the route it calls is listed in [API architecture][arch].

[arch]: ../api-architecture.md
[examples]: https://github.com/harleypig/bw-serve-client/tree/master/examples
[ex-attachments]: https://github.com/harleypig/bw-serve-client/blob/master/examples/attachments.py
[ex-device-approval]: https://github.com/harleypig/bw-serve-client/blob/master/examples/device_approval.py
[ex-folders]: https://github.com/harleypig/bw-serve-client/blob/master/examples/folders.py
[ex-item-fields]: https://github.com/harleypig/bw-serve-client/blob/master/examples/item_fields.py
[ex-org-collections]: https://github.com/harleypig/bw-serve-client/blob/master/examples/org_collections.py
[ex-organizations]: https://github.com/harleypig/bw-serve-client/blob/master/examples/organizations.py
[ex-sends]: https://github.com/harleypig/bw-serve-client/blob/master/examples/sends.py
[ex-socket]: https://github.com/harleypig/bw-serve-client/blob/master/examples/serve_socket.py
[ex-utilities]: https://github.com/harleypig/bw-serve-client/blob/master/examples/utilities.py
[ex-vault-control]: https://github.com/harleypig/bw-serve-client/blob/master/examples/vault_control.py
[ex-vault-items]: https://github.com/harleypig/bw-serve-client/blob/master/examples/vault_items.py
[install]: installation.md
