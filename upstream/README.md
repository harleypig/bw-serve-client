# Upstream

What this repository knows about Bitwarden's Vault Management API, and the
tools that work on it. None of it is part of the installed library.

| File | What it is |
|------|------------|
| `vault-management-api-original.json` | Bitwarden's spec: the raw snapshot, written by detection. It is taken from the [Vault Management API help page][vm-api], which is the only place Bitwarden publishes it. |
| `serve-routes.txt` | The raw snapshot of the routes `bw serve` registers, written by detection. |
| `lock.json` | What detection last recorded about each source, written by detection. |
| `watch.json` | The upstream issues, pull requests and PyPI packages detection watches. Edit it by hand. |
| `spec-fixes.json` | Local fixes, applied to the original spec by `spec_fixes.py`. Described below. |
| `vault-management-api-fixed.json` | The patched spec: the original with the fixes applied. Model generation reads this file. |
| `route-decisions.json` | Recorded decisions on where the spec and `bw serve` disagree. Edit it by hand. |
| `spec_fixes.py` | Applies the fixes, described below. |
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
that changed state, the fixes that no longer match the raw spec, and the
differences between the spec's routes and the routes `bw serve` registers.
The build and check stages fill in its *Regenerated* and *Work created*
sections. The report reflects the latest run only.

Detection applies the fixes to the fetched spec on every run, so a fix that
no longer matches is reported, and detection exits 2, until it is repaired,
even when no source changed. It then compares the patched spec's routes with
the routes `bw serve` registers. A route `bw serve` registers as a pattern,
such as `/object/{object}/{id}`, matches every spec route of that shape, and
parameter names are ignored. A route only the licensed build's configurator
registers is a difference of its own, since the open-source build does not
serve it. A difference recorded under `routes` in `route-decisions.json` is
reported with its decision, matched by shape. Any other difference, and any
recorded decision that no longer matches a difference, also exits 2 until the
file is updated. Behaviour the routes cannot show, such as a handler that
rejects one object type, is recorded by hand under `behaviour`, and is
reported without affecting the exit code.

Detection fetches every source before it writes anything. If any fetch fails,
or returns something it cannot use, it exits 1, names every failure in the
report, and leaves the snapshots and the lock file untouched. It never
commits; committing the result is up to whoever ran it.

Set `GITHUB_TOKEN` to raise the GitHub API rate limit. A run makes about ten
requests, so it works without one.

## The spec fixes

The raw spec cannot be generated as it stands: its schemas lack the titles
that name the generated classes, and a few values are wrong. `spec-fixes.json`
holds the fixes, and `spec_fixes.py` applies them:

```bash
poetry run python upstream/spec_fixes.py apply   # writes vault-management-api-fixed.json
poetry run python upstream/spec_fixes.py check   # reports only
```

The build stage of `pipeline.py` runs `apply`.

Each fix names its target by a path: a list whose strings are object keys and
whose objects select one array element by its fields. A parameter is selected
by `{"in": "query", "name": "search"}`, never by its position, so a fix
survives upstream inserting or reordering parameters:

```json
{
  "op": "set",
  "path": ["paths", "/list/object/items", "get", "parameters",
           {"in": "query", "name": "url"}, "schema", "format"],
  "from": "url",
  "value": "uri",
  "why": "The url filter takes any URI; `uri` is the OpenAPI string format."
}
```

| Op | Does | Fails when |
|----|------|------------|
| `add` | Sets a key to `value`. | The key already exists, which usually means upstream now supplies it. |
| `set` | Replaces the value at the key with `value`. | The current value is not `from`. |
| `delete` | Removes the key. | The current value is not `from`. |
| `append` | Adds `value` to the array at the key. | An element with the same `in` and `name`, or an equal unnamed element, is already there. |

Every fix must also find its target: each key present, each selector matching
exactly one element. `from` makes a `set` or `delete` fail rather than
overwrite a value upstream has changed. When any fix fails, nothing is
written and the run exits 1, naming every fix that failed. `why` is optional;
it explains a fix that changes meaning rather than naming something.

Most fixes add a `title` (which names a generated class or field) or a
`description` (which becomes a docstring). New schemas and parameters follow
the existing convention: the PascalCase name plus `Schema`, such as
`SearchSchema` for a `search` parameter.

## The spec tool

Run it from the repository root:

```bash
poetry run python upstream/api-spec-tool.py <subcommand> [options]
```

| Subcommand | Does |
|------------|------|
| `analyze SPEC` | Summarise the spec's structure: paths, operations, tags. |
| `extract SPEC` | List the routes, as text (the default), Markdown or JSON. `-o FILE` writes to a file. |

Every subcommand takes `-q` for errors only and `-d` for debug output.
`poetry run python upstream/api-spec-tool.py <subcommand> --help` lists the
rest.

Both need only the standard library.

[vm-api]: https://bitwarden.com/help/vault-management-api/
[clients]: https://github.com/bitwarden/clients
