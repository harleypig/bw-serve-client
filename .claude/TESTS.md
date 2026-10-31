# Testing Strategy

**Version:** v1.0.0

Repository-specific testing notes for `bw-serve-client`. General Python
testing tools (pytest, pytest-mock, pytest-cov, tox) are described in
the global `python.md`.

**Precedence:** This file > global `python.md` > global `CLAUDE.md`.

## Layout

Current state:

```text
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
- No authentication header is sent: `bw serve` has no endpoint auth.
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
tox                          # every env: py310–py314 and lint
tox -e py312                 # one Python version
tox -e lint                  # pre-commit check config
```

tox installs each env from the Poetry lockfile, so local runs match CI.
The test envs need Python 3.10–3.14 on `PATH`, and the lint env needs
3.12 (`uv python install 3.10 3.11 3.12 3.13` provides them).

## Examples Directory

Each public API surface MUST have a runnable example in `examples/`.
The directory does not yet exist — create it when the first public API
ships and add an example in the same PR. Examples are not part of the
test suite but MUST stay current; update them when the public API
changes.

## CI

`ci.yml` runs on every pull request and every push to `master`:

- **Tests**: `tox -e py` on each of Python 3.10–3.14.
- **Lint and type check**: `tox -e lint`, which runs the pre-commit check
  config (flake8, pyright and the rest).
- **Generated code is current**: `python pipeline.py build` must regenerate
  nothing and leave the tree clean, so `bw_serve_client/_generated/` never
  drifts from the patched spec and the generator.

Coverage prints in the test log for reading; there is no threshold.
`pyright` is the only type checker. A `mypy` second pass is not run.

`docs.yml` builds and deploys the Sphinx docs separately.
