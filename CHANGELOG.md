# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog][kac].

When `make update` finds that Bitwarden changed something upstream, it
drafts bullets under `## [Unreleased]` between two `draft` comments. Edit
them, move them under the right heading, and delete both comments.

## [Unreleased]

Nothing here has been published to PyPI yet. The library was rebuilt after
the `0.0.4a0` tag; this section covers that rebuild.

### Added

- `ApiClient`, built on httpx: connect by base URL, by Unix socket
  (`unix://<path>`), or through a transport you supply. It is a context
  manager and sends no authentication, since `bw serve` has none. A bare
  IPv6 `domain` such as `::1` is bracketed for you. Proxy settings in the
  environment are ignored and redirects are not followed. A plain `http`
  URL whose host is neither `localhost` nor a loopback address logs a
  warning, since that traffic is unencrypted. A response is parsed as JSON
  only when its media type is exactly `application/json`.
- Resource classes covering every `bw serve` route that works: `Folders`,
  `VaultItems`, `Attachments`, `ItemFields`, `Sends`, `VaultControl`,
  `Utilities`, `Organizations`, `OrgCollections` and `DeviceApproval`,
  each with a runnable example in `examples/`. `OrgCollections.move()` and
  `modify_item_collections()` refuse an empty list of collection ids as a
  `ValidationError` before sending, and `ItemFields.exposed()` reports a
  count that is not an integer as an `ExternalServiceError` carrying the
  status code.
- Pydantic v2 request and response models for every route, generated from
  Bitwarden's Vault Management API spec and exported from the package.
  Request models reject unknown fields; response models ignore them, so a
  field Bitwarden adds does not break a caller. Each route has its own
  path-parameters and query-parameters models, `<Op>PathParameters` and
  `<Op>QueryParameters` (for example `ObjectItemIdDeletePathParameters`),
  and every resource class validates against its own route's models. A
  device-approval request includes its `object` field. The generated route
  list carries each route's spec tags, and model docstrings come from the
  spec's descriptions, written where the spec has none or a wrong one.
- An injectable error handler and logger. Errors derive from
  `BitwardenError`: `ValidationError`, `UserError` (a locked vault, a wrong
  master password), `ExternalServiceError` and `InternalError`. Validation
  and user errors default to WARNING and the others to ERROR, and
  `DefaultErrorHandler` raises them all unless you raise its threshold.
  `bw serve` answers 403 only when it refuses the request's `Host` or
  `Origin` header, so a 403 is a `ValidationError` whose message names the
  `Host` the request sent and the hosts `bw serve` accepts. A non-JSON
  error body longer than 500 characters is cut short in the message.
- Secrets are `SecretStr` and are kept out of errors, logs and reprs. This
  covers the master password and the session key, a Send's password, plus
  a login's password and TOTP, a card's number and code, and the value of
  a hidden custom field, in both the item templates you build and the
  items you read back. To read one, call `get_secret_value()`. A secret is
  revealed only as its request is sent, so error reporters that record
  traceback frame locals (Sentry, rich) cannot show it. `unlock()`,
  `Sends.add()` and `Sends.modify()` accept a password as `str` or
  `SecretStr` and wrap a `str` as soon as they are called.
  `ApiClient.post()` and `put()` accept `SecretStr` values in `data` and
  reveal them the same way. The debug log names query parameters and
  leaves out their values.
- For maintainers: upstream change detection and the update pipeline
  (`make detect`, `build`, `check`, `update`), name-keyed fixes to the
  upstream spec, a comparison of the spec's routes with the ones `bw serve`
  registers, and tests replaying payloads recorded from a real `bw serve`.
  Detection writes every file before renaming any into place, lock file
  last. An interrupted or failed run therefore leaves the snapshots and
  the lock in step, and the next run reports the whole change. A failed
  write ends in the error report and exit 1, as a failed fetch does.
  Detection runs weekly in CI and opens, or updates, an *Upstream change
  detected* issue when it finds a change. Its report warns when recorded
  payloads came from a CLI other than the pinned one, and it hands the
  changelog draft its data directly rather than through the rendered
  report. The text code generation writes lives in `codegen/snippets/`.
- For maintainers: releases. `make release-patch`, `release-minor` and
  `release-major` move the Unreleased entries under a dated version, bump
  the version and tag it in one commit. Pushing the `v*` tag runs the
  release workflow, which tests, builds, creates a GitHub Release from the
  changelog and, once turned on, publishes to PyPI by Trusted Publishing.
- For maintainers: tooling. `poetry install` brings pre-commit. The check
  and fix pre-commit configs run the same hooks, and a test fails when
  they drift apart. CI audits every locked dependency with `pip-audit`, on
  each pull request and weekly, and Dependabot proposes updates for the
  Python dependencies, the actions and the recorder's Docker image. The
  first audit's findings are fixed by updated pins, among them certifi,
  dnspython and idna at runtime. On Python 3.10 dnspython stays at 2.8.0,
  since the fixed release needs 3.11; the library makes no DNS lookups, so
  the vulnerable code is not reached.
- This changelog, with entries drafted by `make update` from the upstream
  change report.
- `examples/serve_socket.py`: starts `bw serve` on a Unix socket, makes one
  call through the library and stops the server.
- `examples/cli.py`: a small command-line app built on the public API
  alone. It lists folders and items and shows an item, masks secrets
  unless asked, gives each error class its own exit status, and has a
  `setup` command that checks the server and the vault.
- Documentation: an API reference built from the docstrings and published
  at <https://harleypig.github.io/bw-serve-client>, installation and quick
  start guides, a page on when to use this library and when to call `bw`
  directly, and a developer guide to the update pipeline. The site also
  has guides: two tutorials (creating and organising items, and a script
  over a Unix socket) and a troubleshooting page keyed on the message you
  see. The repository also holds a record of the pre-1.0 security review,
  a release guide, a contributing guide, a code of conduct, and issue
  forms for bugs and feature requests.

### Changed

- The library is rewritten. The openapi-generator client tagged `0.0.4a0`
  is gone, and none of its API carries over.
- Python 3.10 or later is required.

[kac]: https://keepachangelog.com/en/1.1.0/
[Unreleased]: https://github.com/harleypig/bw-serve-client/compare/0.0.4a0...HEAD
