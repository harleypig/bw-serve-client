# Repository Workflow

**Version:** v1.0.0

Repository-specific workflow for `bw-serve-client`. General rules live in
the global `CLAUDE.md`; Python toolchain rules live in `python.md`.

**Precedence:** This file > global `CLAUDE.md` > global `python.md`.

## Purpose

`bw-serve-client` is a Python client library for the Bitwarden `bw serve`
HTTP API. It is a **library**, not an executable — surface errors by
raising, never by `sys.exit`.

## Repository Layout

| Path                 | Purpose                                  |
|----------------------|------------------------------------------|
| `bw_serve_client/`   | Package source                           |
| `tests/`             | pytest test suite                        |
| `docs/`              | Sphinx docs and architecture notes       |
| `upstream/`          | Detection: the raw snapshots, the lock file, the local fixes, the patched spec, and the detection and spec tools |
| `codegen/`           | Generation inputs: the patched spec becomes `bw_serve_client/models.py` |
| `pipeline.py`        | The update pipeline: detect, build, check, update; exits 0 / 1 / 2 |
| `pyproject.toml`     | Poetry config; tool config inline        |
| `.pre-commit-config.yaml` / `-fix.yaml` | Check / auto-fix configs |

## Error / Logging Module Contract

The error and logging module MUST be agnostic of any specific error
object or logging implementation:

- Accept optional error-handling and logger objects at API-class
  construction. Both are dependency-injected.
- If no error handler is provided, fall back to a minimal built-in that
  constructs and returns error objects based on a configurable error
  level threshold.
- If no logger is provided, fall back to the standard `logging` library.
- Allow callers to set granularity via error-level and log-level
  thresholds.
- Distinguish error types: validation, system, user, external service.

## API Class Contract

Each API class generated from a route MUST:

- Mirror the route name in the method name. When one route name maps to
  multiple HTTP methods, dispatch internally based on parameters.
- Validate parameters with pydantic before issuing the request.
- Format outgoing data into the correct content type for the API.
- Parse responses back into pydantic models.
- Handle authentication (bearer token or whatever the route requires).
- Handle HTTP status codes appropriately and translate failures into
  domain errors.
- Carry over `summary`, `description`, and `tags` from the API
  definition into docstrings; create them if missing.
- Be accompanied by a unit test in `tests/` (use `pytest-mock` for any
  external call) and a usage example in `examples/`.

For the planned class structure and route mapping, see
`docs/api-architecture.md`.

## Pre-commit

Two configs at repo root, per the global `pre-commit.md` policy:

- `.pre-commit-config.yaml` — checks only.
- `.pre-commit-config-fix.yaml` — auto-fix variant.

Run `pre-commit install` once after cloning. Run
`pre-commit run --all-files` before pushing.

## Development Environment

Setup details (Python version, Poetry install, running tests, building
docs) live in `docs/development.md`.

## Branching

Follow the global `git.md` rules. Use the `git-worktree-workflow` skill
for issue branches and PR prep.

## Work Tracking

Open work is tracked as GitHub issues, grouped by milestone on the
[BW Serve Client Library][project] project, where the work is managed,
reported on and tracked. There is no `TODO.md`.

[project]: https://github.com/users/harleypig/projects/3

### Area labels

One `area:*` label per issue, chosen by where the fix lands:

| Label          | Scope                                                                  |
|----------------|------------------------------------------------------------------------|
| `area:detect`  | Upstream change detection: fetchers, snapshots, lock file, change report (`upstream/`) |
| `area:codegen` | Spec fixes, the patched spec, and generation of models and the route list (`codegen/`, `bw_serve_client/_generated/`) |
| `area:library` | Hand-written library code in `bw_serve_client/`: client, transport, errors, resource classes |
| `area:tests`   | Test-suite infrastructure and automated contract and coverage checks (`tests/`) |
| `area:docs`    | Docs, examples, READMEs, and repo conventions as documents             |
| `area:ci`      | CI workflows, scheduled jobs, pre-commit, lint/format/type tooling, packaging config |
