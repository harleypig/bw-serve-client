# Upstream

What this repository knows about Bitwarden's Vault Management API, and the
tool that works on it. None of it is part of the installed library.

| File | What it is |
|------|------------|
| `vault-management-api-original.json` | Bitwarden's spec: the raw snapshot, written by detection. It is taken from the [Vault Management API help page][vm-api], which is the only place Bitwarden publishes it. |
| `serve-routes.txt` | The raw snapshot of the routes `bw serve` registers, written by detection. |
| `lock.json` | What detection last recorded about each source, written by detection. |
| `watch.json` | The upstream issues, pull requests and PyPI packages detection watches. Edit it by hand. |
| `spec-fixes.json` | Local fixes the model generator needs, applied to the original spec. |
| `vault-management-api-fixed.json` | The patched spec: the original with the fixes applied. Model generation reads this file. |
| `detect.py` | Detection, described below. |
| `api-spec-tool.py` | The spec tool, described below. |

The patched spec, not the raw snapshot, is the reference everything else is
built from. Detection only updates the raw snapshots; nothing downstream
changes until the build stage patches the spec again.

## Detection

`detect.py` finds out whether Bitwarden changed anything this library depends
on. It is the `detect` stage of `pipeline.py` at the repository root, which
is the usual way to run it:

```bash
poetry run python pipeline.py detect
```

It checks these sources:

| Source | Recorded in `lock.json` as |
|--------|----------------------------|
| The spec embedded in the help page | its checksum |
| The latest `cli-v*` release of [bitwarden/clients][clients] | the tag |
| The two files that register the `bw serve` routes, as of that release | each file's last commit |
| The routes those files register | the route list's checksum; the list itself is `serve-routes.txt` |
| Each issue and pull request in `watch.json` | its state: open, closed, closed (not planned) or merged |
| Each PyPI package in `watch.json` | its latest version |

Each entry also records `fetched`, the date that content was first fetched.
An unchanged source keeps its date, so a run where nothing changed leaves the
lock file byte for byte as it was.

Every run writes `change-report.md`, which git ignores. It lists the spec's
route, parameter and schema changes, the route changes, the watched items
that changed state, and the fixes in `spec-fixes.json` that no longer match
the raw spec. The build and check stages fill in its *Regenerated* and *Work
created* sections. The report reflects the latest run only.

A fix no longer matches when its target is gone, when the value it records
replacing has changed, when it addresses a named array element by position
and the committed patched spec shows a different element was meant, or when
it adds a value upstream now supplies. That is judged against the current
spec on every run, so detection keeps exiting 2 until the fix is repaired,
even when no source changed.

Detection fetches every source before it writes anything. If any fetch fails,
or returns something it cannot use, it exits 1, names every failure in the
report, and leaves the snapshots and the lock file untouched. It never
commits; committing the result is up to whoever ran it.

Set `GITHUB_TOKEN` to raise the GitHub API rate limit. A run makes about ten
requests, so it works without one.

## The spec tool

Run it from the repository root:

```bash
poetry run python upstream/api-spec-tool.py <subcommand> [options]
```

| Subcommand | Does |
|------------|------|
| `analyze SPEC` | Summarise the spec's structure: paths, operations, tags. |
| `extract SPEC` | List the routes, as text (the default), Markdown or JSON. `-o FILE` writes to a file. |
| `update` | Compare the original and patched specs and add any new differences to `spec-fixes.json`. `--dry-run` shows them without writing. |
| `fix --fixed-file FILE` | Apply `spec-fixes.json` to the original spec and write the result to `FILE`. The path is required, so a plain run never overwrites the committed patched spec. |

Every subcommand takes `-q` for errors only and `-d` for debug output.
`poetry run python upstream/api-spec-tool.py <subcommand> --help` lists the
rest.

`analyze` and `extract` need only the standard library. `update` needs
`deepdiff`, which `poetry install` provides.

[vm-api]: https://bitwarden.com/help/vault-management-api/
[clients]: https://github.com/bitwarden/clients
