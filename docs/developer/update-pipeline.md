# The update pipeline

How to take this library from "Bitwarden may have changed something" to a
branch that is ready to commit: run the pipeline, read its change report,
and do the work it cannot do for you. It is written for a developer or an
AI agent running an update end to end.

The pipeline is `pipeline.py` at the repository root. The detail of each
stage's tools lives beside them, in [`upstream/README.md`][upstream] and
[`codegen/README.md`][codegen]; this guide is the route through them.

## What the pipeline does

| Stage | Does | Writes |
|-------|------|--------|
| `detect` | Compares every upstream source with the lock file; drafts a changelog entry when one changed. | The raw snapshots, the lock file, the change report, a `CHANGELOG.md` draft |
| `build` | Applies the spec fixes to the raw spec, regenerates the package, formats the result. | The patched spec and `bw_serve_client/_generated/` |
| `check` | Runs the test suite. | Its section of the change report |
| `update` | `detect`, then `build`, then `check`, stopping at the first error. | All of the above |

The lock file is `upstream/lock.json`, the change report
`upstream/change-report.md`, the spec fixes `upstream/spec-fixes.json`, and
the patched spec `upstream/vault-management-api-fixed.json`.

Detect checks the spec embedded in Bitwarden's [Vault Management API help
page][vm-api], the latest `cli-v*` release of [bitwarden/clients][clients],
the two files in that release that register the `bw serve` routes and the
routes they register, and the issues, pull requests and PyPI packages listed
in `upstream/watch.json`.

Nothing commits. Every stage leaves its changes in the working tree for you
to review.

## Before you start

- A checkout set up as in [Development setup][dev]: Poetry 2.x and
  `poetry install`, which brings the model generator.
- `pre-commit` on `PATH`. `build` runs its formatter hooks over the
  generated files and fails if it cannot find it.
- Network access for `detect`. `GITHUB_TOKEN` raises the GitHub API rate
  limit; a run makes about ten requests, so it works without one.
- Docker, only if the run calls for re-recording the `bw serve` fixtures
  (*A new CLI release*, below).
- A clean working tree, so what the pipeline changed is all that `git
  status` shows.

## Running it

```bash
make update                             # the same stages, through make
poetry run python pipeline.py update    # when the exit code matters
```

Each stage runs on its own as well: `make detect`, `make build`, `make
check`, or `poetry run python pipeline.py detect` and so on.

Every stage, and `update`, exits with:

| Exit | Means |
|------|-------|
| 0 | No change. Nothing to do. |
| 1 | Error. The stage could not do its job; the report says why. |
| 2 | Change. There is work to do: upstream moved, files were regenerated, or tests fail. |

`make` exits 2 for any recipe that fails, so through `make` an error and a
change look the same. A script, a scheduled job or an agent deciding what
to do next should call `pipeline.py` directly. `update` returns 1 at the
first stage that errors, otherwise the highest of the three stages' codes.

Each stage is idempotent: run again on the same input, it changes nothing
more. The exit code tracks what is still to do, so `detect` keeps exiting
2 while a spec fix no longer matches or a route difference has no
decision, and `check` keeps exiting 2 while a test fails.

**Read the report before you run `detect` again.** Detect moves the lock
file to what it fetched, so on the next run the same upstream change is no
longer a change: the sources table is gone, the report says *No upstream
changes*, and it exits 0. The report reflects the latest run only, and git
ignores it. Copy it somewhere first if you need to keep it.

## Reading the change report

`upstream/change-report.md` opens with one of three summaries:

- **No upstream changes.** Followed, when it applies, by a count of fixes
  that no longer match or route differences that need a decision. Either
  one still makes detect exit 2.
- **N recorded source(s) changed.** Followed by a table of each source
  that moved:

  | Source | Was | Now |
  |--------|-----|-----|
  | cli | cli-v2026.10.0 | cli-v2026.10.1 |

  The source names come from `upstream/lock.json`: `spec`, `cli`,
  `configurators <file>`, `serve_routes`, `watched <issue>` and `packages
  <name>`. Checksums and commits are shortened to twelve characters.
- **Detection failed.** A failed fetch: an *Errors* section names every
  failure, and nothing but the report was written. Fix the cause (often the
  network or the rate limit) and run detect again.

Then a line naming the CLI release and the date the spec was fetched, and
these sections, in this order. Each holds a bullet list, or a one-line note
when it is empty.

| Section | Written by | Lists |
|---------|------------|-------|
| Spec changes | detect | Routes, parameters and schemas the raw spec added, removed or changed |
| Routes bw serve registers | detect | Routes added to or removed from what the CLI registers |
| Watched items | detect | Watched issues and pull requests that changed state; PyPI packages that changed version |
| Fixes that no longer match | detect | Each fix in `upstream/spec-fixes.json` that failed against the new raw spec, by number, op and path |
| Spec vs CLI routes | detect | Each route the spec and `bw serve` disagree on: undecided ones, then stale decisions, then decided ones |
| Recorded behaviour | detect | The hand-recorded differences the route comparison cannot see, from `upstream/route-decisions.json` |
| Regenerated | build | The files build changed, or *Nothing; the generated files were already current* |
| Work created | check | Each failing or erroring test, or *None; every test passes* |
| Changelog | detect | Whether a changelog entry was drafted; present only when a source changed |

Until build and check run, their sections read *Not run*. Running `build`
or `check` on its own replaces only its own section; `detect` rewrites the
whole report.

## What to do for each kind of change

Work down the report. One upstream release often shows up in several
sections at once; a new CLI release, for example, can move `cli`, both
`configurators` rows and `serve_routes` together.

### A spec change

Bitwarden changed the spec on its help page. *Spec changes* says what.

1. Run `build`. It applies the fixes to the new raw spec and regenerates
   the models and the route list; *Regenerated* names what changed.
2. Run `check`, and work through *Work created*:
   - `tests/test_docstrings.py` fails when a route's summary or caveat
     changed. Each resource method's docstring carries its route's spec
     text, so copy the new text into the method by hand.
   - `tests/test_route_coverage.py` fails on a spec route that no resource
     method declares, and on a declared route the spec no longer has.
     Implement the new route in a resource class, or list it in
     `tests/route_exclusions.json` with the reason it is left out.
   - `tests/test_spec_examples.py` fails when an example in the patched
     spec no longer validates against its generated model, or carries a
     key the model has no field for.
3. A route a resource method gained or lost also means updating its row in
   [API architecture][arch] and its example in `examples/`.

### A fix that no longer matches

Each fix in `upstream/spec-fixes.json` names its target and, for a `set` or
`delete`, the value it expects to find there, so it fails rather than
overwrite a value upstream changed. The report names the fix by number.
While any fix fails, `build` writes nothing and exits 1, so `update` stops
there.

Read the fix's `why`, when it has one, and the new raw spec at that path,
then decide:

- **Upstream fixed it.** Delete the fix.
- **Upstream moved or renamed the target.** Update the fix's `path`, or
  its `from`.
- **Upstream changed the value, and the fix is still needed.** Update
  `from` to the new value.

The op table in [`upstream/README.md`][upstream] *The spec fixes* says when
each op fails. Then confirm every fix matches again:

```bash
poetry run python upstream/spec_fixes.py check   # silent, exit 0
```

### A route difference: the route decision

*Spec vs CLI routes* compares the patched spec's routes with the routes
`bw serve` registers. Routes match by shape, ignoring parameter names, and
a route only the licensed build registers is a difference of its own. Each
difference reads one of three ways:

- **documented, but bw serve registers no matching route**
- **registered by bw serve, but not documented**
- **registered only by the licensed build**

A line ending *needs a decision* has no entry in
`upstream/route-decisions.json`. Decide what the library does about it,
and record it under `routes`, keyed by `METHOD /path`, with the decision
as the value. A line ending *recorded decision matches no difference any
more; remove it* is a decision upstream made unnecessary: delete it. Either
kind keeps detect exiting 2 until the file is updated, so run `detect`
again afterwards to confirm the section holds only decided routes. Once the
report shows nothing new, that second run is harmless.

A decision usually has a second half: a route the library will not offer
goes in `tests/route_exclusions.json` with its reason, and a route it does
offer gets a resource method.

Some differences the routes cannot show, such as a handler that answers 400
for one object type. Those go under `behaviour` in
`upstream/route-decisions.json`, by hand. They appear under *Recorded
behaviour* and never affect the exit code.

### A new CLI release

`cli` moved in the sources table. Three things are pinned to the CLI
release, and the lock file now names a new one:

1. **The enumerated request fields.** `tests/test_request_enums.py` was read
   from the Bitwarden source at one release, recorded as `READ_AT`.
   `test_values_were_read_at_the_locked_release` fails on every CLI bump
   with *re-read every source cited in test_request_enums.py at
   \<release\>, then update READ_AT*. Re-read each file the table cites, at
   the new tag; where a value was added or dropped, update both the table
   and the spec fix that sets that enum; last, set `READ_AT` to the new
   release.
2. **The recorded fixtures.** The payloads in `tests/fixtures/serve/` were
   recorded against the pinned CLI. Re-record them against the new release:

   ```bash
   poetry run python tests/fixtures/recorder/record.py   # needs Docker
   ```

   It builds an image holding the CLI release named in
   `upstream/lock.json`, starts it beside a throwaway Vaultwarden with a
   made-up account, records every case, redacts every secret, and removes
   the containers, the network and the image (`--keep-image` keeps the
   image; `--port` moves `bw serve` off 8087). Payloads are written only
   once every case answered and was redacted. Review the diff of
   `tests/fixtures/serve/` as you would code: a changed status or body is a
   change in `bw serve`'s behaviour.
3. **The recorded-fixture tests.** Run `check`.
   `tests/test_recorded_fixtures.py` replays every payload through the
   library, and `test_every_payload_has_an_expectation` fails in both
   directions when a case was added or dropped. Where a recording and the
   library now disagree, either fix the library or the spec, or mark the
   case in `MISMATCHES` with the disagreement as its reason, which makes it
   a strict `xfail`. The resource tests and `tests/test_docstrings.py` are
   worth reading in the same pass, since a behaviour change usually lands in
   a method's docstring too.

A new release can also move the `configurators` rows and `serve_routes`;
those show up under *Routes bw serve registers* and *Spec vs CLI routes*,
above.

### A watched item or package

An issue or pull request in `upstream/watch.json` closed or merged, or a
watched PyPI package released. Nothing regenerates. Read the item, then
find the code that cites it, such as the `Host` header workaround in
`bw_serve_client/api_client.py` that cites bitwarden/clients#22867:

```bash
git grep -n 'bitwarden/clients#22867'
```

Decide whether the workaround can go, and whether the item still needs
watching. `upstream/watch.json` is edited by hand.

## The changelog draft

When the report has a sources table, `detect` drafts an entry directly
under `## [Unreleased]` in `CHANGELOG.md`:

```markdown
<!-- draft 486a9ee9ea20: written by the update pipeline from the change report.
Edit these, move them under Added, Changed or Fixed, then delete both
draft comments. -->

- Upstream `cli`: cli-v2026.10.0 → cli-v2026.10.1
- Upstream `packages bitwarden-sdk`: 2.0.0 → 2.1.0

<!-- end draft 486a9ee9ea20 -->
```

One bullet per changed source, then one per *Spec changes* bullet and one
per *Routes bw serve registers* bullet. The key is a hash of the bullets,
so a second run on the same report adds nothing, and nothing outside the
block is touched. The outcome is the report's *Changelog* section; it
never changes the exit code.

Nothing is drafted when detect failed, when no source changed (a stale fix
or an undecided route alone is no change a user sees), or when
`CHANGELOG.md` is missing or has no `## [Unreleased]` heading.

The draft is raw material. Rewrite each bullet in terms a user of the
library would recognise, move it under *Added*, *Changed* or *Fixed*, drop
what a user would not notice (a watched issue changing state, usually),
and delete both comments. Do it on the same branch: by the next run the
lock file has moved, and detect drafts nothing more for this change.

## What stays manual

The pipeline detects, regenerates and tests. These are yours:

- **Discrepancy decisions.** Each route difference in
  `upstream/route-decisions.json`, each excluded route in
  `tests/route_exclusions.json`, and each stale spec fix.
- **Behaviour tests.** Re-recording the fixtures against a new CLI, reading
  their diff, and recording behaviour the routes cannot show under
  `behaviour`. Nothing runs a live `bw serve` except the recorder.
- **The enum re-read** behind `READ_AT`, at every CLI bump.
- **Resource code** for a new route, with its unit test and its example in
  `examples/`.
- **Docs.** Method docstrings when a spec summary or caveat changes, the
  [API architecture][arch] tables when a route is added or removed, and the
  changelog draft.
- **The commit.** CI's *Generated code is current* job runs
  `pipeline.py build` and fails if anything it writes differs from what is
  committed, so commit the regenerated files with the rest.

## A worked run

These are the commands this guide was checked with, on 2026-11-02, at CLI
release `cli-v2026.10.1`.

`build` and `check`, in a checkout where nothing upstream had moved:

```console
$ poetry run python pipeline.py build; echo "exit=$?"
build: nothing to regenerate
exit=0
$ make build; echo "exit=$?"
build: nothing to regenerate
exit=0
$ poetry run python pipeline.py check
...
1311 passed in 5.40s
$ poetry run python upstream/spec_fixes.py check; echo "exit=$?"
exit=0
```

Afterwards the report held only the two sections those stages write:

```markdown
## Regenerated

Nothing; the generated files were already current.

## Work created

None; every test passes.
```

`detect`, against the live sources (it only reads them; with nothing
changed upstream it rewrites the lock file and snapshots byte for byte as
they were):

```console
$ poetry run python pipeline.py detect; echo "exit=$?"
detect: no upstream changes
exit=0
```

Its report opened *No upstream changes.* and listed the five device-approval
routes under *Spec vs CLI routes*, each *registered only by the licensed
build* with its recorded decision, and the item-collections route under
*Recorded behaviour*.

To see a change, `detect` was run again in a scratch copy of
`pipeline.py`, `CHANGELOG.md` and `upstream/`, with that copy's
`upstream/lock.json` edited back to `cli-v2026.10.0` and `bitwarden-sdk`
2.0.0:

```console
$ python pipeline.py detect; echo "exit=$?"
detect: 2 source(s) changed; see .../upstream/change-report.md
detect: Drafted an entry under `## [Unreleased]` in `CHANGELOG.md` (draft 486a9ee9ea20); edit it and delete its draft comments.
exit=2
$ python pipeline.py detect; echo "exit=$?"
detect: no upstream changes
exit=0
```

The first run wrote the sources table and the draft shown in *The
changelog draft*; the package also appeared under *Watched items*. The
second shows why the report comes first: the lock file had moved, so the
same change was no longer one.

From there, a real update would continue as *A new CLI release* describes:
re-read the enum sources and set `READ_AT`, re-record the fixtures, run
`check`, rewrite the changelog draft, and commit.

Not run for this guide: `update` as one command (its three stages were run
one by one above), and the fixture recorder, which builds a Docker image
and runs the CLI against a throwaway Vaultwarden and has nothing to
re-record while the CLI release is unchanged.

[arch]: ../api-architecture.md
[clients]: https://github.com/bitwarden/clients
[codegen]: ../../codegen/README.md
[dev]: ../development.md
[upstream]: ../../upstream/README.md
[vm-api]: https://bitwarden.com/help/vault-management-api/
