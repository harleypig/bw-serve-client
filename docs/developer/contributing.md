# Contributing

How a change gets into `bw-serve-client`, from the issue to the release.
Setting up a checkout to work in is [Development Setup][dev]. Everyone
taking part follows the [code of conduct][coc].

## Start from an issue

Work is tracked as [GitHub issues][issues], grouped by milestone on the
[BW Serve Client Library project][project]. Look there before starting, and
open an issue for anything larger than a typo so the change has somewhere
to be discussed. [New issue][new-issue] offers two forms, a bug report and
a feature request; a problem in `bw serve` itself belongs in
[Bitwarden's tracker][bw-issues] instead.

## Report a security issue

Do not open a public issue for a vulnerability. Report it privately through
GitHub's [private vulnerability reporting][advisory]. Only the repository's
maintainers can read the report, so it stays private until a fix ships.
The [security policy][security] says which versions get fixes.

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

Write each commit summary as a sentence in the imperative that says what
the change does, with the issue number after it, such as `Fix the
StatusSchema and UrisSchema descriptions (#89)`. Give the pull request's
title the same form: pull requests are squash-merged, so the title usually
becomes the commit on `master`.

CI runs on every pull request:

- the tests on Python 3.10 through 3.14,
- the pre-commit check config (`tox -e lint`), and
- a rebuild of the generated code, which must leave the tree unchanged.

A pull request that touches `docs/`, `bw_serve_client/`, `pyproject.toml`,
`poetry.lock` or the docs workflow also builds the Sphinx docs, with
warnings as errors: a docstring that doesn't render, or a public name with
no page, fails it.

## Release

A release closes the changelog's `## [Unreleased]` section, bumps the
version and tags it in one commit, with `make release-patch`, `-minor` or
`-major`; pushing the tag runs the release workflow. The whole procedure,
and the one-time setup for publishing to PyPI, is [Releasing][releasing].

[advisory]: https://github.com/harleypig/bw-serve-client/security/advisories/new
[bw-issues]: https://github.com/bitwarden/clients/issues
[changelog]: ../../CHANGELOG.md
[coc]: ../../CODE_OF_CONDUCT.md
[new-issue]: https://github.com/harleypig/bw-serve-client/issues/new/choose
[conventions]: ../../.claude/CONVENTIONS.md
[dev]: ../development.md
[examples]: https://github.com/harleypig/bw-serve-client/tree/master/examples
[issues]: https://github.com/harleypig/bw-serve-client/issues
[project]: https://github.com/users/harleypig/projects/3
[releasing]: releasing.md
[security]: ../../.github/SECURITY.md
[tests]: ../../.claude/TESTS.md
[workflow]: ../../.claude/WORKFLOW.md
