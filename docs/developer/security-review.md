# Security Review

A review of credential handling, secure defaults and transport guidance in
`bw-serve-client`, made on 2026-11-03 against `master` at `38f4b13`. Each
finding below is open unless marked fixed; line numbers are at that commit.

## Scope

- **Credential handling**: which values are `SecretStr`, where they are
  revealed, and whether any path puts one in an exception, a log record, a
  repr, a traceback frame, the injected error handler or logger, or a retry.
- **Error messages**: whether text from the server reaches an exception.
- **Transport**: TCP and Unix socket, bind address, the `Host` and `Origin`
  check, TLS, socket permissions, and what the README and docs say of each.
- **Client defaults**: timeouts, redirects, proxies and other environment
  settings httpx reads, certificate verification.
- **Dependencies and supply chain**: the audit in CI, Dependabot, actions.
- **Recorded fixtures**: whether a recording can carry a secret.

Out of scope: `bw serve` itself, Vaultwarden, and penetration testing.

## Method

Each claim was read in the code, then checked by running it where running
was possible. Probes used made-up secrets, a mock transport and two local
HTTP servers; no real vault was touched.

- Read `api_client.py`, `resource.py`, `errors.py`, every resource class,
  the generated models, `tests/test_secrets.py` and the fixture recorder.
- Probed: `HTTP_PROXY` and `ALL_PROXY` pointed at a recording proxy, with
  the client and with a bare `httpx.Client` for contrast; `repr`, `str`,
  `model_dump` in both modes, `model_dump_json` and `pickle` of an item
  holding a login password and TOTP; validation failures carrying a
  password under a misspelt name and as the wrong type; a 400 and a 500
  whose bodies echo a secret; the traceback frames of a rejected
  `Sends.add` and of a rejected `VaultControl.unlock` given a `str`, using
  the frame walk in `tests/test_secrets.py`; the DEBUG log of a query.
- Read `apps/cli/src/commands/serve.command.ts` and
  `apps/cli/src/serve.program.ts` at `cli-v2026.10.1` for the bind address,
  the `Host` and `Origin` checks, and how the socket is created.
- Ran `pip-audit` 2.10.1 against the exported lock (all groups, hashes,
  `--strict`) on Python 3.14, and `trivy fs` for vulnerabilities and
  secrets over the tree.

Severity: **Medium** defeats a protection the library claims; **Low**
weakens one, or leaves a hazard to the caller; **Info** is a note.

## Findings

### F1 — A master password given as `str` stays in traceback frames (Medium)

**Evidence.** `VaultControl.unlock` takes `Union[str, SecretStr]`
(`bw_serve_client/vault_control.py:54`), and the README and example pass a
`str` from `getpass` (`README.md:299`, `examples/vault_control.py:59`).
The plaintext stays in `unlock`'s `password` and in `Resource._request`'s
`body`, `unvalidated`, `fields` and `raw` (`resource.py:283-292`) until the
model wraps it. A rejected unlock given a `str` left it in those five
locals; given a `SecretStr`, in none. The no-frame guarantee of #97 holds
only for the second, and `tests/test_secrets.py` tests only that.

**Recommendation.** Rebind `password = SecretStr(password)` as the first
statement of `unlock`, so no library frame keeps the `str`. Show
`SecretStr(getpass(...))` in the README and the example, so the caller's
frame does not either. Add a `str` case to `TestTracebackLocals`.

### F2 — A Send's password is revealed before validation (Medium)

**Evidence.** `_template` calls `get_secret_value()` on the Send password
before the body is validated (`bw_serve_client/sends.py:64-65`), and
`SendTemplateSchema.password` is a plain `str`
(`bw_serve_client/_generated/models.py:1379`), so the password stays plain
all the way to the request. A rejected
`Sends.add(..., password=SecretStr(...))` left it in `add`'s `body`; in
`_request`'s `body`, `validated`, `unvalidated`, `fields`, `raw` and
`dumped`; and in `_make_request`'s `data`, `body` and `serialized_data`.
The caller's `SecretStr` buys nothing.

**Recommendation.** Give `send.template` `password` `format: password` in
`upstream/spec-fixes.json`, as #124 did for the item fields; drop the early
reveal; extend `TestTracebackLocals` to `Sends.add` and `Sends.modify`.

### F3 — Free-text fields that commonly hold secrets are plain `str` (Low)

**Evidence.** Item `notes` (`models.py:591`, `:1443`), a secure note,
`ItemFields.notes`, and a Send's `text` and `notes` (`models.py:170`,
`:628`, `:655`) are plain strings, as are identity `ssn`, `passportNumber`
and `licenseNumber` (`models.py:88-91`, `:502-505`). The identity fields
were left unmasked on purpose, but no issue, doc or test records that
choice, and nothing records one for notes or Send text. Text Sends exist
to share secrets; their text is in reprs and, on failure, in frames.

**Recommendation.** Decide the masking scope for notes and Send text,
and record it, with the identity decision, in `docs/api-architecture.md`.
Mask Send `text` at least.

### F4 — An error message carries the server's body text (Low)

**Evidence.** `_handle_error` uses the JSON `message`, or for a body that
is not JSON the whole `response.text`
(`bw_serve_client/api_client.py:404-413`). A 400 and a 500 whose bodies
held a made-up secret both raised with it in the message, which the
default handler also logs. `bw serve` sends fixed messages, and the server
behind it never sees plaintext, so no echo was found in practice; the
exposure is to whatever else answers on the port, such as a proxy's or
another program's HTML page.

**Recommendation.** Cap a non-JSON body in the message (a few hundred
characters) and say it was cut; keep the JSON `message` as it is.

### F5 — Query values are logged at DEBUG (Low)

**Evidence.** `_make_request` logs `Query parameters: {params}`
(`bw_serve_client/api_client.py:247`), values included, while the body is
logged by field name only (line 252). The probe logged a `search` term in
full. Search terms and `url` filters can name what is in the vault.

**Recommendation.** Log query parameter names only, as for the body.

### F6 — The safe client defaults are httpx's, and nothing pins them (Low)

**Evidence.** The client ignores `HTTP_PROXY`, `HTTPS_PROXY` and
`ALL_PROXY` only because it always passes a transport
(`api_client.py:163`, `:179`, `:188`): httpx turns environment proxies off
when it is given one (`httpx/_client.py:685` in 0.28.1). The probe
confirmed it: the client reached the target, while a bare `httpx.Client`
in the same environment sent the request, and so would have sent a master
password, to the proxy. `trust_env` is still `True`. Redirects are not
followed only because httpx defaults `follow_redirects` to `False`. No test
covers either, so a refactor that drops the explicit transport, or an httpx
change, would route localhost traffic through a proxy unnoticed.

**Recommendation.** Pass `trust_env=False` and `follow_redirects=False`
to `httpx.Client` explicitly, and test that a proxy set in the environment
receives nothing.

### F7 — No warning when a password would cross a network in the clear (Low)

**Evidence.** `ApiClient` builds `http://<domain>` for any `domain`
(`bw_serve_client/api_client.py:169-176`) without remark. `bw serve` has no
TLS, so a non-loopback address sends the master password and every vault
secret unencrypted.

**Recommendation.** Log a WARNING when the scheme is `http` and the host is
not a loopback address or `localhost`. The README now says to use an SSH
tunnel instead (F8).

### F8 — Transport guidance left out three ways to widen access (Low, fixed)

**Evidence.** The README said `--hostname all` exposes the server to the
network, and that a socket readable only by its owner is tighter. Upstream,
`--hostname all` also switches the `Host` check off
(`serve.command.ts:96`), `--disable-origin-protection` switches the `Host`
and `Origin` checks off (`serve.command.ts:85`), and the socket is created
by a plain `server.listen(socketPath)` with no `chmod`
(`serve.command.ts:134-137`), so who can connect is the umask's and the
directory's choice. Nothing said `bw serve` has no TLS.

**Fixed in this change.** The README's paragraph on who can reach the
server now names both flags, says to use neither, says to use an SSH tunnel
rather than plain HTTP between machines, and says to create the socket in a
directory only you can enter, such as `$XDG_RUNTIME_DIR`.
`examples/serve_socket.py` already does that, with a private
`TemporaryDirectory`.

### F9 — The unvalidated client methods return secrets unmasked (Info)

**Evidence.** `ApiClient.get`, `post`, `put` and `delete`
(`api_client.py:449-515`) return the parsed JSON, so a login password read
through them is a plain `str` in a `dict`. Their docstrings warn that they
skip validation, not that they skip masking.

**Recommendation.** Add that to the four docstrings.

### F10 — A pickled model carries its secrets (Info)

**Evidence.** `pickle.dumps` of an item with a `SecretStr` password
contains the plaintext; pydantic pickles a `SecretStr`'s value. `repr`,
`str`, `model_dump` (both modes) and `model_dump_json` do not.

**Recommendation.** One sentence in the README's secrets section: do not
pickle or cache models holding secrets.

### F11 — Python 3.10 keeps a vulnerable `dnspython` (Low)

**Evidence.** On 3.10 the lock pins `dnspython` 2.8.0, which has
CVE-2026-114605 (HIGH, a DoS parsing DNS responses), and `filelock` 4.1.0;
the fixes need 3.11, so `.github/workflows/security.yml:56-73` ignores
their advisories on 3.10. `filelock` is a development dependency only.
`dnspython` is a runtime one (`pydantic[email]` → `email-validator`), but
the vulnerable path is unreachable from this library: pydantic calls
`validate_email(..., check_deliverability=False)`
(`pydantic/networks.py:1405` in 2.14.2), which makes no DNS query. Python
3.10 reached end of life in October 2026.

**Recommendation.** Write the reachability reason into the comment above
the ignore list, and drop Python 3.10, which removes the list.

### F12 — Supply-chain hardening gaps (Info)

**Evidence.** Every workflow uses first-party actions by major tag
(`actions/checkout@v7` and others), not by commit SHA. Commit-time secret
scanning is `detect-private-key` alone; there is no general secret scanner
in pre-commit or CI. No `SECURITY.md` exists, though
`docs/developer/contributing.md` and the issue template point to private
vulnerability reporting.

**Recommendation.** Pin actions by SHA (Dependabot keeps SHA pins
current); add `gitleaks` to both pre-commit configs; add a short
`SECURITY.md` pointing at the existing reporting route.

## Checked and found sound

- **Secret coverage.** `SecretStr` holds the master password and session
  key (`UnlockPostRequestSchema.password`, `LockUnlockDataSchema.raw` and
  `.message`); login password and TOTP; card number and code;
  password-history passwords; SSH private key; bank account number, PIN and
  IBAN; passkey `keyValue`; attachment `url`; a Send's `key`, `accessUrl`
  and `password` as returned; `/generate`, `/object/password` and
  `/object/totp` results; and hidden custom-field values on both request
  and response models (#94, #124, #150).
- **Revealed at send time only.** `_reveal` runs inside `ApiClient._send`
  (`api_client.py:314`); `Resource._request` reveals path and query only,
  never the body (`resource.py:297`). Rejected item adds and modifies
  leave no secret in any frame (`TestTracebackLocals`, #126).
- **Nothing kept after sending.** `_send` replaces the response's request
  with one that has no body (`api_client.py:334`), and turns a transport
  failure into a copy with no request and no traceback on its cause chain
  (`api_client.py:320-327`).
- **Validation messages.** `_summarize` drops pydantic's input values
  (`resource.py:178`). A password under a misspelt field name and one of
  the wrong type both produced messages without the value.
- **Logging.** The body is logged by field name only
  (`api_client.py:252`); the default error handler logs the category and
  message only (`errors.py:276`); the package logger has a `NullHandler`
  and no level, so nothing is emitted unless the application asks.
- **Retries.** `HTTPTransport(retries=...)` retries failed connections
  only; a request that reached the server is never sent again, and an error
  status is never retried.
- **Host and Origin.** The client sends no `Origin`. Over a socket it sends
  `Host: localhost:<port>`, which `bw serve` accepts (`api_client.py:167`);
  a 403 names the `Host` sent, not any secret.
- **Defaults.** `localhost:8087`, matching `bw serve`; a 30-second timeout
  on connect, read, write and pool; certificate verification on for
  `https`, with no option to turn it off short of a caller's own transport.
- **Docs.** The README, `docs/when-to-use.md`,
  `docs/user/installation.md` and the Sphinx index all say the library
  sends no credentials and that whatever reaches the listener can use the
  unlocked vault.
- **Recorded fixtures.** The recorder replaces every secret with
  `<redacted>` before writing (`tests/fixtures/recorder/record.py`), and
  `tests/test_recorded_fixtures.py` derives the secret field names from the
  generated models and fails on any unredacted one. `trivy fs` found no
  secret in the tree.
- **Dependencies.** `pip-audit` found no known vulnerability in the locked
  pins on Python 3.14. The `Security` workflow audits every supported
  Python weekly and on every pull request; its last run on `master`
  passed. Dependabot covers pip, GitHub Actions and the recorder's Docker
  image. `bandit` runs in pre-commit.
- **Workflow permissions.** Each workflow sets `contents: read` and adds
  only what it needs (`issues: write` for detection, Pages for docs); none
  runs on `pull_request_target`.

## Sources

- `bw serve`'s bind address, `Host` and `Origin` checks and socket
  creation: `apps/cli/src/commands/serve.command.ts` and
  `apps/cli/src/serve.program.ts` in [bitwarden/clients][clients] at
  `cli-v2026.10.1`, read 2026-11-03.
- httpx environment proxies and redirect default: `httpx/_client.py`,
  httpx 0.28.1 as locked.
- pydantic's email validation: `pydantic/networks.py`, pydantic 2.14.2 as
  locked.

[clients]: https://github.com/bitwarden/clients
