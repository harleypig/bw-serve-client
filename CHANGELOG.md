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
  manager and sends no authentication, since `bw serve` has none.
- Resource classes covering every `bw serve` route that works: `Folders`,
  `VaultItems`, `Attachments`, `ItemFields`, `Sends`, `VaultControl`,
  `Utilities`, `Organizations`, `OrgCollections` and `DeviceApproval`,
  each with a runnable example in `examples/`.
- Pydantic v2 request and response models for every route, generated from
  Bitwarden's Vault Management API spec and exported from the package.
  Request models reject unknown fields; response models ignore them, so a
  field Bitwarden adds does not break a caller.
- An injectable error handler and logger. Errors derive from
  `BitwardenError`: `ValidationError`, `UserError` (a locked vault, a wrong
  master password), `ExternalServiceError` and `InternalError`. Validation
  and user errors default to WARNING and the others to ERROR, and
  `DefaultErrorHandler` raises them all unless you raise its threshold.
- Secrets such as the master password and the session key are `SecretStr`
  and are kept out of errors, logs and reprs.
- For maintainers: upstream change detection and the update pipeline
  (`make detect`, `build`, `check`, `update`), name-keyed fixes to the
  upstream spec, a comparison of the spec's routes with the ones `bw serve`
  registers, and tests replaying payloads recorded from a real `bw serve`.
- This changelog, with entries drafted by `make update` from the upstream
  change report.

### Changed

- The library is rewritten. The openapi-generator client tagged `0.0.4a0`
  is gone, and none of its API carries over.
- Python 3.10 or later is required.

[kac]: https://keepachangelog.com/en/1.1.0/
[Unreleased]: https://github.com/harleypig/bw-serve-client/compare/0.0.4a0...HEAD
