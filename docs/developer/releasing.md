# Releasing

How a version of `bw-serve-client` is cut and published. One command on
`master` closes the changelog, bumps the version and tags it; pushing the
tag runs the [release workflow][workflow], which tests, builds and creates
the GitHub Release. Publishing to PyPI is a further job in that workflow,
off until the [one-time setup](#publishing-to-pypi) is done.

## Before you start

- Be on `master`, up to date with `origin/master`, with a clean working
  tree. The release commit is made there and pushed directly.
- Finish the changelog. Everything under `## [Unreleased]` in
  [`CHANGELOG.md`][changelog] is what gets released, so read it as the
  release notes it is about to become. When `make update` has drafted
  entries from an upstream change, edit them, move them under Added,
  Changed or Fixed, and delete both `draft` comments. The release refuses
  while either comment is still there, and refuses an empty Unreleased.

## Cut the release

Pick the part to bump, following [Semantic Versioning][semver]:

```bash
make version-show     # print the current version
make release-patch    # 0.1.1 -> 0.1.2: fixes
make release-minor    # 0.1.1 -> 0.2.0: new features, backward compatible
make release-major    # 0.1.1 -> 1.0.0: breaking changes
```

Each runs `python release.py prepare <part>`, which:

1. refuses a dirty working tree, or a tag that already holds the next
   version;
2. moves the Unreleased entries under `## [X.Y.Z] - YYYY-MM-DD` (today, in
   UTC), leaves an empty `## [Unreleased]` above them, and points the
   compare links at the foot of the changelog at the new tag;
3. runs `bump2version`, which updates the version in `pyproject.toml`,
   `bw_serve_client/__init__.py` and `.bumpversion.cfg`, and commits all of
   it with the changelog as `Bump version: A → B`, tagged `vX.Y.Z`.

If the bump fails before it commits, the working tree is put back as it
was. Nothing is pushed. Look at the commit with `git show`, then publish
it:

```bash
git push origin master vX.Y.Z
```

The `make version-*` targets bump and tag without touching the changelog;
use `release-*` to release.

## What the workflow does

Pushing a `v*` tag runs `.github/workflows/release.yml`:

1. **Tests** on Python 3.10 through 3.14, as CI does.
2. **Check the tag and build.** The tag must equal `v` plus the version in
   `pyproject.toml`, `__version__` must match it, and the tagged commit
   must be on `master`. The notes come from the changelog's section for
   the version (`python release.py notes X.Y.Z`), which must exist, must
   not be empty and must hold no draft. Then `poetry build` makes the
   wheel and the sdist.
3. **GitHub Release** named after the tag, with that section as its notes
   and the wheel and sdist attached.
4. **Publish to PyPI**, only when the repository variable `PYPI_PUBLISH`
   is `true`, and only after the GitHub Release exists, since an upload to
   PyPI cannot be taken back.

Watch it with `gh run watch`, or on the [Actions page][actions].

## When something goes wrong

A pushed tag is never moved or deleted. If the workflow fails, fix the
cause on `master` and release the next patch version. The failed tag stays
behind with no GitHub Release, and the next release's compare link starts
from it.

## Publishing to PyPI

The `pypi` job uses [PyPI Trusted Publishing][trusted]: PyPI accepts an
upload from this repository's release workflow with no API token stored
anywhere. It needs three things set up once, by an owner of the repository
and of the PyPI account:

1. **A pending publisher on PyPI.** The project does not exist on PyPI
   yet, so register it as a [pending publisher][pending]: log in to PyPI,
   open *Publishing* in your account's sidebar, choose *GitHub*, and
   enter:

   | Field | Value |
   |-------|-------|
   | PyPI project name | `bw-serve-client` |
   | Owner | `harleypig` |
   | Repository name | `bw-serve-client` |
   | Workflow name | `release.yml` |
   | Environment name | `pypi` |

   The first successful upload creates the project and turns the pending
   publisher into an ordinary one.

2. **A `pypi` environment on GitHub.** Under *Settings* → *Environments* →
   *New environment*, name it `pypi`. Restrict its deployment branches and
   tags to tags matching `v*`, and add yourself as a required reviewer if
   each upload should wait for your approval. From the command line, the
   environment alone is:

   ```bash
   gh api --method PUT repos/harleypig/bw-serve-client/environments/pypi
   ```

3. **Turn the job on**:

   ```bash
   gh variable set PYPI_PUBLISH --body true --repo harleypig/bw-serve-client
   ```

The next tag pushed publishes. A tag pushed before this setup is not
published; the workflow does not run again for it. Once the
package is on PyPI, update the installation instructions in
[`README.md`][readme] and [the installation guide][install], which still
say to install from git.

[actions]: https://github.com/harleypig/bw-serve-client/actions/workflows/release.yml
[changelog]: ../../CHANGELOG.md
[install]: ../user/installation.md
[pending]: https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/
[readme]: ../../README.md
[semver]: https://semver.org/
[trusted]: https://docs.pypi.org/trusted-publishers/
[workflow]: ../../.github/workflows/release.yml
