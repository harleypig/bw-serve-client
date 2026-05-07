# Coding Conventions

**Version:** v1.0.0

Repository-specific overrides for `bw-serve-client`. General style rules
live in the global `code-style.md`; Python conventions and toolchain live
in the global `python.md`.

**Precedence:** This file > global `python.md` > global `code-style.md` >
global `CLAUDE.md`.

## Formatter

This repo uses **yapf + isort** (not black). The yapf style is defined
inline in `pyproject.toml` under `[tool.yapf]`:

- `based_on_style = "google"`
- `indent_width = 2`
- `column_limit = 132`
- `dedent_closing_brackets = true`

`column_limit = 132` applies to **code lines only**. Comments still wrap
at 72 columns per the global `code-style.md`; widen a comment past 72
only when absolutely needed (e.g., an unbreakable URL or a long literal
that would mislead if split).

`flake8` is configured in `pyproject.toml` under `[tool.flake8]` with
`max-line-length = 132` to match yapf, and disables the rules that
conflict with 2-space indent and the yapf/pydocstringformatter ruleset
(see the file for the full ignore list).

## Type Checking

This repo uses `pyright` only — both locally and in pre-commit. `mypy`
is not currently configured. The global `python.md` recommends `mypy`
as a CI second pass; when CI test workflows are added to this repo,
consider whether to enable that mypy pass.
