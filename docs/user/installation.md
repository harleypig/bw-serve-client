# Installation

`bw-serve-client` talks to `bw serve`, the local HTTP server built into the
Bitwarden CLI. Using it takes two things: the Python package, and a
`bw serve` it can reach.

## The package

The package needs Python 3.10 or later. It is not published to PyPI;
install it from the git repository.

With pip:

```bash
pip install git+https://github.com/harleypig/bw-serve-client
```

With Poetry, in your own project:

```bash
poetry add git+https://github.com/harleypig/bw-serve-client.git
```

Either installs the current `master`. To pin a commit, append `@<commit>`
to the URL.

The runtime dependencies are `httpx` and `pydantic`. To check the install:

```bash
python -c "import bw_serve_client; print(bw_serve_client.__version__)"
```

## A running `bw serve`

The library sends no credentials. `bw serve` has no authentication on its
endpoints: the session lives in the `bw serve` process, so whatever can
reach its address can use the unlocked vault. Keep it on `localhost`, its
default.

1. **Install the Bitwarden CLI** (`bw`), from a native executable, npm
   (`npm install -g @bitwarden/cli`), Chocolatey, Snap or Flatpak.
   Bitwarden's [CLI documentation][cli-install] covers each.
2. **Log in** once with `bw login`.
3. **Unlock and start the server.** `bw unlock` prints a session key;
   export it as `BW_SESSION` and `bw serve` starts with the vault unlocked:

   ```bash
   export BW_SESSION="$(bw unlock --raw)"
   bw serve
   ```

   `bw serve` listens on `localhost:8087` by default. `--port` and
   `--hostname` change that ([`bw serve` options][cli-serve]).

   You can also start `bw serve` locked and unlock it from Python with
   `VaultControl(client).unlock(password)`; see
   [`examples/vault_control.py`][ex-vault-control].

Next: the [quick start][quick-start].

[cli-install]: https://bitwarden.com/help/cli/#download-and-install
[cli-serve]: https://bitwarden.com/help/cli/#serve
[ex-vault-control]: https://github.com/harleypig/bw-serve-client/blob/master/examples/vault_control.py
[quick-start]: quick-start.md
