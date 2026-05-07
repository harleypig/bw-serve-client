# Testing Strategy

**Version:** v1.0.0

Repository-specific testing notes for `bw-serve-client`. General Python
testing tools (pytest, pytest-mock, pytest-cov, tox) are described in
the global `python.md`.

**Precedence:** This file > global `python.md` > global `CLAUDE.md`.

## Layout

Current state:

```
tests/
└── test_<module>.py     # One test file per source module
```

Each `bw_serve_client/<module>.py` SHOULD have a paired
`tests/test_<module>.py`. Add `tests/conftest.py` for shared fixtures and
`tests/fixtures/` for recorded API payloads when the suite outgrows
ad-hoc fixtures.

## What to Test

Per the API class contract in `WORKFLOW.md`, every API class MUST have
unit tests covering:

- Parameter validation (success and failure).
- Request body construction.
- Response parsing into pydantic models.
- HTTP status handling (success, 4xx, 5xx).
- Authentication header injection.
- Error path: how errors propagate through the injected error handler.

## Mocking

Use `pytest-mock` for any external call. Do not hit a live `bw serve`
instance from unit tests. Recorded fixtures in `tests/fixtures/` are the
source of truth for response shapes.

## Running

```bash
pytest                       # full suite
pytest tests/test_foo.py     # single file
pytest -k "auth"             # by keyword
pytest --cov=bw_serve_client # with coverage
tox                          # all supported Python versions
```

## Examples Directory

Each public API surface MUST have a runnable example in `examples/`.
The directory does not yet exist — create it when the first public API
ships and add an example in the same PR. Examples are not part of the
test suite but MUST stay current; update them when the public API
changes.

## CI

Currently only `docs.yml` runs in GitHub Actions. A workflow that runs
`pytest` (and optionally `mypy`) on every push and pull request is
planned; until it exists, agents MUST run `pytest` locally before
pushing.
