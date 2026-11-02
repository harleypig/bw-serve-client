# Development Setup

How to get a working checkout of `bw-serve-client`: install it, run the
tests and the checks, and build the docs. How to propose a change is in the
[contributing guide][contrib].

None of this needs a running `bw serve`. The test suite mocks every HTTP
call and replays responses recorded from a real one.

## Prerequisites

- **Python 3.10 or later.** One version is enough to develop and run the
  tests. Running every tox env needs 3.10, 3.11, 3.12, 3.13 and 3.14 on
  `PATH`, and the lint env needs 3.12. `uv python install 3.10 3.11 3.12
  3.13 3.14` is one way to get them.
- **[Poetry][poetry] 2.x.** CI pins 2.5.1.
- **[pre-commit][pre-commit]**, installed on its own (for example with
  `pipx install pre-commit`). It is not one of the project's Poetry
  dependencies, so `poetry install` does not provide it.
- **Git.**

## Install

```bash
git clone https://github.com/harleypig/bw-serve-client.git
cd bw-serve-client
poetry install
pre-commit install
```

`poetry install` creates the virtualenv and installs the package with every
dependency group: the runtime dependencies plus `dev`, `test` and `docs`.
`pre-commit install` adds the git hook that runs the check config on each
commit.

## Run the tests

```bash
poetry run pytest                          # the full suite, with coverage
poetry run pytest tests/test_folders.py    # one file
poetry run pytest -k unlock                # by keyword
make test                                  # the full suite
```

Coverage prints at the end of every run. It is there to read; no threshold
fails the build.

tox runs the suite on each supported Python, installing every env from the
Poetry lockfile so a local run matches CI:

```bash
poetry run tox              # py310 to py314, then lint
poetry run tox -e py312     # one Python version
poetry run tox -e lint      # the pre-commit check config
```

To pass pytest arguments through tox, put `--` after `poetry run` as well,
since Poetry otherwise takes the second `--` for itself:
`poetry run -- tox -e py312 -- -k unlock`.

What the suite covers and how it is laid out is in
[`.claude/TESTS.md`][tests].

## Run the checks

The repo has two pre-commit configs:

| Config | What it does |
|--------|--------------|
| `.pre-commit-config.yaml` | Checks only: yapf, flake8, pyright, bandit, markdownlint, yamllint and the rest. The git hook and CI run this one. |
| `.pre-commit-config-fix.yaml` | The auto-fix variant: it rewrites files (yapf, isort, whitespace, `poetry lock`) and then checks them. |

```bash
make format    # run the fix config over every file
make lint      # run the check config over every file
```

Run both before you push. To check only the files you changed, pass them to
pre-commit directly:

```bash
pre-commit run --config .pre-commit-config-fix.yaml --files <files>
pre-commit run --files <files>
```

pyright is the only type checker. Run it, and flake8 and bandit, through
pre-commit: the hooks pin their versions and run pyright on Python 3.12,
while a bare `poetry run pyright` on Python 3.14 cannot parse that
version's standard library. The formatter is yapf (2-space indent,
132-column code lines), not black; the settings are in `pyproject.toml` and
the reasons in [`.claude/CONVENTIONS.md`][conventions].

## Regenerate the generated code

`bw_serve_client/_generated/` is built from the patched Bitwarden spec, and
CI fails if it is out of date. After a change to the spec fixes or the
generator, rebuild it and commit the result:

```bash
poetry run python pipeline.py build
```

The update pipeline as a whole (`detect`, `build`, `check`, `update`), and
what to do with each kind of change it reports, is in the [update pipeline
guide][pipeline].

## Build the docs

The Sphinx docs live in `docs/html/` and deploy to GitHub Pages from CI:

```bash
cd docs/html
poetry run sphinx-build -W -b html source _build/html
```

Open `docs/html/_build/html/index.html` to read the result.

## Where the rest lives

- [Contributing][contrib]: issues, branches, pull requests and releases.
- [API architecture][arch]: how the resource classes map to the routes.
- [`.claude/WORKFLOW.md`][workflow]: the repository layout and the contracts
  every resource class and the error module follow.

[arch]: api-architecture.md
[contrib]: developer/contributing.md
[conventions]: ../.claude/CONVENTIONS.md
[poetry]: https://python-poetry.org/docs/#installation
[pre-commit]: https://pre-commit.com/#install
[pipeline]: developer/update-pipeline.md
[tests]: ../.claude/TESTS.md
[workflow]: ../.claude/WORKFLOW.md
