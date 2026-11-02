# Bitwarden CLI Vault Management API

A Python client for the [Bitwarden Vault Management API][vm-api], the HTTP
API that the Bitwarden CLI serves with `bw serve`.

If you're looking for Bitwarden's public API, for organization management,
that is the [Bitwarden Public API][public-api], a different thing.

The library talks to a `bw serve` that is already running. It does not log
in, start `bw serve`, or hold a session key: the session lives in the
`bw serve` process, and no request this library sends carries a key or a
token. See [Starting `bw serve`](#starting-bw-serve).

[public-api]: https://bitwarden.com/help/api/

## Use this library, or call `bw` directly?

Not every job needs a server. A shell script that reads one password is
shorter and simpler with `bw get password`; a program that makes many calls,
in Python, gains from one unlocked `bw serve` and typed results. Both sides,
each point checked against the CLI, are in
[When to use this library][when-to-use].

[when-to-use]: docs/when-to-use.md

## Generated Code

The data models and the route list in `bw_serve_client/_generated/` are
generated from Bitwarden's published OpenAPI spec for the Vault Management
API. The models are pydantic 2 models, and the package exports them, so
callers write `from bw_serve_client import FolderSchema`. The resource
classes that call the API, such as `bw_serve_client/folders.py`, are written
by hand.

Bitwarden publishes the spec only inside its [Vault Management API help
page][vm-api]. There is no standalone JSON file, and the spec's own version
is always `latest`. A copy of it is committed in `upstream/`, along with the
local fixes the generator needs and the patched spec they produce.

`pipeline.py` keeps it current in three stages: `detect` reports whether
Bitwarden changed anything, `build` patches the spec and regenerates
`bw_serve_client/_generated/`, and `check` runs the tests. `update` runs all
three. Running them on a schedule is planned on the [project board][project].

```bash
poetry run python pipeline.py update   # or detect, build, check
```

Each stage exits 0 when nothing changed, 1 on an error, and 2 when something
changed and there is work to do. `make detect`, `make build`, `make check`
and `make update` run the same stages, but make exits 2 for every failure, so
call `pipeline.py` directly when the exit code matters. The [update pipeline
guide][pipeline-guide] walks through a run and what to do with each kind of
change.

| Path | What it holds |
|------|---------------|
| `pipeline.py` | The update pipeline's entry point. |
| `upstream/` | The committed Bitwarden spec and the other upstream snapshots, the lock file, the local fixes, the patched spec, and the detection and spec tools. See `upstream/README.md`. |
| `codegen/` | Inputs to model generation. See `codegen/README.md`. |

[pipeline-guide]: docs/developer/update-pipeline.md
[vm-api]: https://bitwarden.com/help/vault-management-api/
[project]: https://github.com/users/harleypig/projects/3

## Requirements

* Python 3.10+

* The [Bitwarden CLI][cli-download], to run `bw serve`. It need not be on
  the machine running your Python, as long as your code can reach the
  server. Installation is covered in the
  [CLI documentation][cli-install].

[cli-download]: https://bitwarden.com/download/#downloads-command-line-interface
[cli-install]: https://bitwarden.com/help/cli/#download-and-install

## Starting `bw serve`

The library needs three things done outside it, all with the `bw` CLI.

1. **Log in**, once per device. `bw serve` refuses to start for a logged-out
   CLI.

   ```bash
   bw login                # email and master password, prompted
   bw login --apikey       # or with a personal API key
   ```

2. **Unlock**, so `bw serve` starts with an unlocked vault. `bw unlock`
   prints a session key; export it as `BW_SESSION` in the shell that starts
   the server.

   ```bash
   export BW_SESSION="$(bw unlock --raw)"
   ```

   You can skip this step and start the server locked instead: every vault
   call then fails with a `UserError` until something unlocks it over HTTP,
   which [`VaultControl.unlock`](#unlocking-over-http) does.

3. **Start the server.** It listens on `localhost:8087` by default.

   ```bash
   bw serve                                # http://localhost:8087
   bw serve --port 8088                    # another port
   bw serve --hostname unix:///run/user/1000/bw.sock   # a Unix socket
   ```

**The session key goes to `bw serve`, never to this library.** `bw unlock`
generates the key that decrypts the vault, and `bw` commands read it from
`BW_SESSION` or `--session` ([CLI: Using a session key][cli-session]).
`bw serve` is one of those commands, so it holds the key for as long as it
runs, and no endpoint asks a client for one. The key is valid until `bw lock`
or `bw logout`, or `POST /lock` (`VaultControl.lock`), invalidates it.

While the server runs, anything that can reach it can read the vault. It
binds to `localhost` unless told otherwise, and `--hostname all` exposes it
to the network ([CLI: serve][cli-serve]). A Unix socket, readable only by
its owner, is the tighter choice on a shared machine.

[cli-session]: https://bitwarden.com/help/cli/#using-a-session-key
[cli-serve]: https://bitwarden.com/help/cli/#serve

## Installation

The package is not on PyPI yet. Install it from the repository:

```sh
pip install git+https://github.com/harleypig/bw-serve-client.git
```

or, in a Poetry project:

```sh
poetry add git+https://github.com/harleypig/bw-serve-client.git
```

To work on the library itself, see [Development Setup][development].

[development]: docs/development.md

## Usage

The examples below need a running `bw serve`, unlocked except in
[Unlocking over HTTP](#unlocking-over-http). A snippet that only builds an
`ApiClient` makes no request, and runs without one.

### Connecting

`ApiClient` holds the connection. Each group of routes is a resource class
built from it: `Folders`, `VaultItems`, `Attachments`, `ItemFields`, `Sends`,
`VaultControl`, `Utilities`, `Organizations`, `OrgCollections` and
`DeviceApproval`.

```python
from bw_serve_client import ApiClient, VaultControl

with ApiClient(base_url="http://localhost:8087") as client:
  status = VaultControl(client).status()
  print(status.status.value)  # "unlocked", "locked" or "unauthenticated"
```

`ApiClient()` with no arguments connects to `http://localhost:8087`. For a
server on a Unix socket, pass the socket as the URL:

```python
from bw_serve_client import ApiClient

client = ApiClient(base_url="unix:///run/user/1000/bw.sock")
```

The client sends `Host: localhost:8087` over a socket, because `bw serve`
refuses requests whose `Host` it does not expect. If the server was started
with `--port`, pass the same `port=` to `ApiClient`.
[`examples/serve_socket.py`][serve-socket] starts `bw serve` on a socket,
makes one call through it and stops the server.

### Reading and writing

Results come back as pydantic models, and secrets as `SecretStr`, which
stays hidden in a `repr`, a log record or an error message until you call
`get_secret_value()`.

```python
from bw_serve_client import ApiClient, Folders, ItemFields, VaultItems

with ApiClient() as client:
  items = VaultItems(client)

  for item in items.list(search="github"):
    print(item.id, item.name)

  login = items.get(search="GitHub")  # one match, or a ValidationError
  password = ItemFields(client).password(login.id)
  print(password)  # **********

  folder = Folders(client).add("Projects")
  print(folder.id, folder.name)
```

### Seeing your own writes

`bw serve` can answer a read from local state that does not yet include a
write it just made: a `list` straight after an `add` can come back without
the new item. When the next read must see the write, sync in between.

```python
from bw_serve_client import ApiClient, VaultControl, VaultItems

with ApiClient() as client:
  items = VaultItems(client)
  note = items.add({"type": 2, "name": "Example note", "secureNote": {"type": 0}})

  VaultControl(client).sync()
  print(note.id in [item.id for item in items.list()])  # True
```

An empty item list can also come back right after a sync, reported upstream
as [bitwarden/clients#23283][bw-23283] (open).

[bw-23283]: https://github.com/bitwarden/clients/issues/23283

### Handling errors

Every failure raises a subclass of `BitwardenError`: `ValidationError` for a
bad request or an id that names nothing, `UserError` for a locked vault or a
wrong password, `ExternalServiceError` when `bw serve` fails or cannot be
reached, and `InternalError` for a bug in this library. Each carries the
HTTP `status_code`, or `None` when there was no response.

```python
from bw_serve_client import ApiClient, UserError, ValidationError, VaultItems

with ApiClient() as client:
  try:
    item = VaultItems(client).get("00000000-0000-0000-0000-000000000000")

  except UserError:
    print("The vault is locked")

  except ValidationError as error:
    print(f"No such item: {error} (HTTP {error.status_code})")
```

To get validation and user errors back as values instead of exceptions,
raise the handler's threshold. A method then returns the error in place of
its result. Any object that implements `ErrorHandler` can replace the
default handler the same way.

```python
import logging

from bw_serve_client import ApiClient, DefaultErrorHandler

app_log = logging.getLogger("myapp.bitwarden")

client = ApiClient(logger=app_log, error_handler=DefaultErrorHandler(error_level=logging.ERROR, logger=app_log))
```

The client's `logger` receives its request and response records. A handler
you construct logs errors to its own `logger`, so give it the same one; only
the default handler is wired to the client's logger for you.

A resource class takes `error_handler=` to override the client's for that
class alone. Its `logger=` receives only the class's one-line request trace;
request and response records still go to the client's logger, and errors to
the error handler.

### Unlocking over HTTP

A server started locked can be unlocked through the library. The method
sends the master password to `bw serve` and returns the session key as a
`SecretStr`; nothing in this library needs it afterwards, since `bw serve`
keeps the session.

```python
from getpass import getpass

from bw_serve_client import ApiClient, VaultControl

with ApiClient() as client:
  VaultControl(client).unlock(getpass("Master password: "))
```

## Reference

* [API architecture][api-architecture] lists every resource class, its
  methods and the route each one calls.
* [`examples/`][examples] has a runnable script for each resource class.
  Each needs a running, unlocked `bw serve`, and reads `BW_SERVE_URL` for
  its address, except `serve_socket.py`, which starts its own `bw serve` on
  a Unix socket.
* The [documentation site][docs-site] has the API reference built from the
  docstrings.

[api-architecture]: docs/api-architecture.md
[examples]: examples/
[serve-socket]: examples/serve_socket.py
[docs-site]: https://harleypig.github.io/bw-serve-client
