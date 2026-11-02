# When to Use This Library, and When to Call `bw`

Both routes end at the same Bitwarden CLI. A direct call starts `bw` once
per command; this library talks to one long-running `bw serve` over HTTP.
This page is for deciding which suits your case. Neither list below is the
default, and the points under each were checked against the CLI release the
library tracks, `cli-v2026.10.1` (*Sources*, at the end).

## When the library helps

### Many calls, without paying for a CLI start on each

Every `bw` command starts the CLI again, and on the machine measured here
that costs about three seconds a call, whatever the command. `bw serve`
pays that once, then answers each request in milliseconds.

| Call | Per call |
|------|----------|
| `bw status` | 3,032 ms |
| `bw list items` | 3,355 ms |
| `bw list folders` | 3,077 ms |
| `VaultControl(client).status()` | 20.6 ms |
| `VaultItems(client).list()` | 4.2 ms |
| `Folders(client).list()` | 1.0 ms |

`bw serve` was answering 1.1 seconds after it was launched. The figures are
means over ten calls, after one warm-up call, against a throwaway
Vaultwarden 1.37.4 holding a near-empty vault, with CLI 2026.10.1 in a
container on a 4-core Linux host. Expect your numbers to differ; the gap,
seconds against milliseconds, is the finding.

### No session key on each call

A direct call needs the session key on every command, from `BW_SESSION` or
from `--session`. A key passed with `--session` is in the command line,
which a process listing shows to other users on the same machine, and
`BW_SESSION` is in the environment of every process that inherits it. The
library sends no key at all: `bw serve` holds the session. If you unlock
through the library (`VaultControl.unlock`), the master password travels
once, in a request body to `bw serve`.

### Validated requests, typed results

The CLI already prints JSON, so a direct call means building the input and
parsing the output yourself. The library checks a request against
pydantic models before it is sent, and returns models, with secrets as
`SecretStr` so they stay out of logs and reprs.

### Errors you can tell apart

Every failed `bw` command exits with status 1 (0 if `BW_CLEANEXIT` is set)
and prints a message, so telling a locked vault from a missing item means
reading the message. The library raises a typed exception for each kind:
`UserError` for a locked vault or a wrong password, `ValidationError` for a
bad request or an id that names nothing, `ExternalServiceError` when
`bw serve` fails or cannot be reached.

### No arguments to encode

`bw create` and `bw edit` take the object as base64-encoded JSON, as an
argument or on standard input, so a script runs `bw encode` and builds the
command line, quoting item names as it goes. The library takes a dict or a
model. From Python, `subprocess` with a list of arguments already avoids
the shell; the gain is largest over a shell script.

### Testable without a vault

`ApiClient` takes any httpx transport, so tests can answer requests with
`httpx.MockTransport` and never start a server. Testing code that shells
out to `bw` means faking the executable or its output.

## When calling `bw` directly is better

### A few calls from a script

`bw get password <item>` in a shell script is one line, needs no server
and no Python packages. The library needs `bw serve` started, waited on,
and stopped afterwards. Speed is not the reason to prefer it here, since a
server is answering before one `bw` call finishes (above); the reason is
the server to manage. In CI, or in a container that makes a few calls and
exits, that management is most of the work.

### Not writing Python

The library is Python only. From any other language, call `bw`, or talk to
`bw serve` over HTTP yourself; the [Vault Management API][vm-api] is
documented by Bitwarden.

### What `bw serve` does not expose

The library can only do what `bw serve` offers, and these CLI commands have
no `bw serve` route: `login`, `logout`, `config` (choosing the server),
`import`, `export`, `report`, `receive`, `encode`, `update`, `completion`,
`sdk-version`, and `serve` itself. Logging in is always a `bw` step, before
the server can start.

### An unlocked vault behind a listener

While `bw serve` runs, the vault stays unlocked, and anything that can reach
its listener can read it. On `localhost` that is every process on the
machine, any user's. `bw serve` refuses requests carrying an `Origin`
header or an unexpected `Host`, which stops a web page from reaching it
through a browser, but not a local program. A Unix socket, readable only by
its owner, narrows that to one user; `--hostname all` widens it to the
network. A direct call holds no listener open, though a session key kept in
`BW_SESSION` stays valid until `bw lock` or `bw logout` too.

### Fewer moving parts

The library adds a server process to supervise and Python dependencies to
keep current. It also follows the `bw serve` API, so a CLI release that
changes the API can break it until the library catches up.

### The library is young

It is classed as beta and not on PyPI. Its interface may still change.

### Machine secrets: Secrets Manager

For secrets that applications and pipelines need, rather than a person's
vault, Bitwarden sells [Secrets Manager][sm]: secrets grouped into
projects, read by machine accounts with access tokens. Its
[SDK][sm-sdk] has a Python wrapper, and a [CLI][sm-cli] of its own, and
needs no `bw serve` at all. It is a separate product with its own plans.

## Sources

- The per-call times: measured 2026-11-02 with `@bitwarden/cli` 2026.10.1
  and `vaultwarden/server:1.37.4`, using the fixture recorder's container
  setup (`tests/fixtures/recorder/`), the library from this repository on
  the host, `bw` and `bw serve` in the container.
- Session key, `--session`, `BW_SESSION`, `bw lock` and `bw logout`:
  [Password Manager CLI][cli], *Using a session key*.
- `bw serve`'s defaults, `--hostname all` and origin protection:
  [Password Manager CLI][cli], *serve*; the `Host` check is
  `apps/cli/src/commands/serve.command.ts` at `cli-v2026.10.1`.
- Exit status 1 on every failure: `apps/cli/src/base-program.ts` at
  `cli-v2026.10.1`.
- Encoded JSON for `create`: `apps/cli/src/vault.program.ts` at
  `cli-v2026.10.1`.
- Commands without a route: the commands registered in
  `apps/cli/src/program.ts`, `vault.program.ts`, `tools/send/send.program.ts`
  and `dirt/report.program.ts`, against the routes in
  `apps/cli/src/oss-serve-configurator.ts`, all at `cli-v2026.10.1`; the
  route list is also `upstream/serve-routes.txt` in this repository.
- Secrets Manager: [Secrets Manager Overview][sm] and
  [Secrets Manager SDK][sm-sdk], fetched 2026-11-02.

[cli]: https://bitwarden.com/help/cli/
[vm-api]: https://bitwarden.com/help/vault-management-api/
[sm]: https://bitwarden.com/help/secrets-manager-overview/
[sm-sdk]: https://bitwarden.com/help/secrets-manager-sdk/
[sm-cli]: https://bitwarden.com/help/secrets-manager-cli/
