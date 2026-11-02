# Contributing

How a change gets into `bw-serve-client`, from the issue to the release.
Setting up a checkout to work in is [Development Setup][dev].

## Start from an issue

Work is tracked as [GitHub issues][issues], grouped by milestone on the
[BW Serve Client Library project][project]. Look there before starting, and
open an issue for anything larger than a typo so the change has somewhere
to be discussed.

Each issue carries one `area:` label, chosen by where the fix lands:

| Label | Where |
|-------|-------|
| `area:detect` | Upstream change detection (`upstream/`) |
| `area:codegen` | Spec fixes and code generation (`codegen/`, `bw_serve_client/_generated/`) |
| `area:library` | The hand-written library in `bw_serve_client/` |
| `area:tests` | Test infrastructure and the automated checks (`tests/`) |
| `area:docs` | Docs, examples and READMEs |
| `area:ci` | CI, pre-commit, packaging and tooling config |

## Make the change

Branch from `master` with a name that says what the branch is for, such as
`fix/109-recorder-volumes` or `feature/m7-resource-classes`.

What a change owes depends on what it touches:

- **A resource class or a public method** follows the API class contract in
  [`.claude/WORKFLOW.md`][workflow]: pydantic validation, typed errors,
  docstrings carried over from the spec. It needs unit tests (see
  [`.claude/TESTS.md`][tests] for what they cover) and a runnable example in
  [`examples/`][examples], kept current when the public API changes. The
  suite fails if a resource class has no example.
- **The spec fixes or the generator** need the generated code rebuilt with
  `poetry run python pipeline.py build` and committed. CI fails when
  `bw_serve_client/_generated/` does not match what the generator produces.
- **A bug fix** adds a test that fails without the fix.
- **A change to behaviour** updates the docs that describe it, in the same
  pull request, and adds a line to [`CHANGELOG.md`][changelog] under
  `## [Unreleased]`.

Code style is yapf with 2-space indents, 132-column code lines and comments
wrapped at 78; the details are in [`.claude/CONVENTIONS.md`][conventions].
Markdown is GitHub-flavoured, wrapped at 78 columns, with reference-style
links.

## Check it

Before you push, run the fix config and then the check config, and the
tests:

```bash
make format
make lint
poetry run tox
```

[Development Setup][dev] has the narrower forms of each.

## Open a pull request

Push the branch and open a pull request against `master`. Say what changed
and why, and put `Closes #N` on a line of its own for each issue it
finishes.

CI runs on every pull request:

- the tests on Python 3.10 through 3.14,
- the pre-commit check config (`tox -e lint`), and
- a rebuild of the generated code, which must leave the tree unchanged.

A pull request that touches `docs/` also builds the Sphinx docs.

## Release

The package is not published to PyPI; users install it from this
repository. A release is a finished changelog and a version bump.

Finish the changelog first. When Bitwarden changes something upstream,
`make update` drafts entries under `## [Unreleased]` between two `draft`
comments; edit them, move them under the right heading, and delete both
comments. Then give the released entries a heading for the new version,
as [Keep a Changelog][kac] describes.

Bump the version with `bump2version`, through the Makefile:

```bash
make version-show     # print the current version
make version-patch    # 0.1.1 -> 0.1.2: fixes
make version-minor    # 0.1.1 -> 0.2.0: new features, backward compatible
make version-major    # 0.1.1 -> 1.0.0: breaking changes
```

Each bump updates the version in `pyproject.toml`,
`bw_serve_client/__init__.py` and `.bumpversion.cfg`, then commits and tags
it as `v<version>`, so it needs a clean working tree. To see what a bump
would change without making it, run `poetry run bump2version --dry-run
--verbose patch`; the dry run refuses a dirty tree too, unless you add
`--allow-dirty`. The configuration is `.bumpversion.cfg`.

[changelog]: ../../CHANGELOG.md
[conventions]: ../../.claude/CONVENTIONS.md
[dev]: ../development.md
[examples]: https://github.com/harleypig/bw-serve-client/tree/master/examples
[kac]: https://keepachangelog.com/en/1.1.0/
[issues]: https://github.com/harleypig/bw-serve-client/issues
[project]: https://github.com/users/harleypig/projects/3
[tests]: ../../.claude/TESTS.md
[workflow]: ../../.claude/WORKFLOW.md
