#!/usr/bin/env python3

"""Run the update pipeline: detect, build, check, or all three.

Usage: ``python pipeline.py {detect,build,check,update}``

Stages:

- ``detect``: fetch every upstream source and write the snapshots, the lock
  file and the change report (``upstream/detect.py``). When a recorded
  source changed, draft a changelog entry from the report (below).
- ``build``: patch the spec, regenerate ``bw_serve_client/_generated/``, and
  format the result.
- ``check``: run the test suite.
- ``update``: detect, then build, then check. Stops at the first error.

Every stage, and ``update``, exits:

- 0: no change. Nothing changed, nothing to do.
- 1: error. The stage could not do its job.
- 2: change. Something changed and there is work to do: upstream moved,
  files were regenerated, or tests fail.

Run it directly, not through ``make``, when the exit code matters: make
exits 2 for every failed recipe, so it cannot tell an error from a change.
Each stage is idempotent: run again on the same input, it changes nothing
more. The exit code reflects what is still to do, so detect keeps exiting 2
while a fix no longer matches, and check while a test fails.

Changelog drafts: when the change report lists changed sources, detect
inserts a bullet list directly under ``## [Unreleased]`` in
``CHANGELOG.md``, one bullet per changed source, spec change and route
change, between a ``<!-- draft <key>`` comment and an
``<!-- end draft <key> -->`` one. The key is a hash of the bullets, so a
second run on the same report adds nothing, and nothing outside the
inserted block is touched. A person edits the bullets, moves them under
Added, Changed or Fixed, and deletes both comments; by then the lock file
has moved, so detect drafts nothing more until upstream changes again. A
missing changelog, or one with no ``## [Unreleased]`` heading, gets no
draft. The outcome goes in the report's Changelog section and never
changes the exit code.
"""

import hashlib
from pathlib import Path
import re
import shutil
import subprocess  # noqa: S404 - runs this repo's own tools with fixed arguments. # nosec B404
import sys
from typing import Callable, Dict, List, Optional

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "upstream" / "change-report.md"
CHANGELOG = ROOT / "CHANGELOG.md"
PATCHED_SPEC = ROOT / "upstream" / "vault-management-api-fixed.json"
GENERATED = ROOT / "bw_serve_client" / "_generated"
FORMAT_HOOKS = ("trailing-whitespace", "end-of-file-fixer", "isort", "yapf", "pydocstringformatter")

NO_CHANGE, ERROR, CHANGE = 0, 1, 2


class StageError(Exception):
  """A stage could not do its job."""


# -----------------------------------------------------------------------------
def relative(path: Path) -> str:
  """Return a path relative to the repository root, for messages.

  Arguments:
      path: A path inside the repository.

  Returns:
      str: The relative path.
  """
  return str(path.relative_to(ROOT))


# -----------------------------------------------------------------------------
def run_tool(args: List[str]) -> "subprocess.CompletedProcess[str]":
  """Run a command from the repository root, capturing its output.

  Arguments:
      args: The command and its arguments.

  Returns:
      subprocess.CompletedProcess[str]: The finished process.
  """
  return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=False)  # noqa: S603 - fixed arguments. # nosec B603


# -----------------------------------------------------------------------------
def set_report_section(title: str, lines: List[str], empty: str) -> None:
  """Replace one ``## title`` section of the change report, or add it.

  Starts a report when detect has not written one, so a stage run alone
  still leaves its result on record.

  Arguments:
      title: The section heading, without the ``##``.
      lines: The bullet items.
      empty: The line to show when there are no items.
  """
  text = REPORT.read_text(encoding="utf-8") if REPORT.exists() else "# Upstream change report\n\n"
  body = "\n".join(f"- {line}" for line in lines) if lines else empty
  section = f"## {title}\n\n{body}\n"

  pattern = re.compile(rf"^## {re.escape(title)}\n.*?(?=^## |\Z)", re.MULTILINE | re.DOTALL)
  match = pattern.search(text)
  if match:
    text = f"{text[:match.start()]}{section}\n{text[match.end():]}".rstrip("\n") + "\n"

  else:
    text = f"{text.rstrip(chr(10))}\n\n{section}"

  REPORT.write_text(text, encoding="utf-8")


# -----------------------------------------------------------------------------
def report_items(text: str, title: str) -> List[str]:
  """Return the bullet items of one ``## title`` section of a report.

  Arguments:
      text: The report.
      title: The section heading, without the ``##``.

  Returns:
      List[str]: The items without their bullet; empty when the section is
      missing or holds only its "None." note.
  """
  match = re.search(rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
  return [line[2:] for line in match.group(1).splitlines() if line.startswith("- ")] if match else []


# -----------------------------------------------------------------------------
def changelog_draft(text: str) -> List[str]:
  """Turn a change report into draft changelog bullets.

  Only the sources table decides whether there is anything to draft:
  detect also exits 2 for a stale fix or an undecided route, and neither
  is a change a user of the library would see.

  Arguments:
      text: The change report.

  Returns:
      List[str]: The bullets, or none when no recorded source changed.
  """
  # Rows of detect's "| Source | Was | Now |" table, header excluded.
  rows = re.findall(r"^\| (.+?) \| (.*?) \| (.*?) \|$", text, re.MULTILINE)
  sources = [f"Upstream `{name}`: {was} → {now}" for name, was, now in rows if name != "Source"]
  if not sources:
    return []

  return [
    *sources,
    *(f"Upstream spec: {line}" for line in report_items(text, "Spec changes")),
    *(f"bw serve routes: {line}" for line in report_items(text, "Routes bw serve registers")),
  ]


# -----------------------------------------------------------------------------
def draft_changelog() -> None:
  """Draft a changelog entry from the change report, once per report.

  Inserts only the marked block under ``## [Unreleased]``; see the module
  docstring for the format. The outcome goes in the report.
  """
  bullets = changelog_draft(REPORT.read_text(encoding="utf-8")) if REPORT.exists() else []
  if not bullets:
    return

  key = hashlib.sha256("\n".join(bullets).encode("utf-8")).hexdigest()[:12]
  text = CHANGELOG.read_text(encoding="utf-8") if CHANGELOG.exists() else None
  heading = re.search(r"^## \[Unreleased\][^\n]*\n", text, re.MULTILINE) if text is not None else None

  if text is None:
    outcome = f"No draft: `{CHANGELOG.name}` is missing."

  elif heading is None:
    outcome = f"No draft: `{CHANGELOG.name}` has no `## [Unreleased]` heading."

  elif f"<!-- draft {key}" in text:
    outcome = f"Already drafted in `{CHANGELOG.name}` (draft {key}); nothing added."

  else:
    block = "\n".join([
      f"<!-- draft {key}: written by the update pipeline from the change report.",
      "Edit these, move them under Added, Changed or Fixed, then delete both",
      "draft comments. -->",
      "",
      *(f"- {bullet}" for bullet in bullets),
      "",
      f"<!-- end draft {key} -->",
      "",
    ])
    CHANGELOG.write_text(f"{text[:heading.end()]}\n{block}{text[heading.end():]}", encoding="utf-8")
    outcome = f"Drafted an entry under `## [Unreleased]` in `{CHANGELOG.name}` (draft {key}); edit it and delete its draft comments."

  set_report_section("Changelog", [outcome], "")
  print(f"detect: {outcome}")


# -----------------------------------------------------------------------------
def build_outputs() -> "tuple[Path, ...]":
  """List the files build writes, as they are on disk now.

  The generated package is globbed, so a module the generator adds is
  formatted and compared without being listed here too.

  Returns:
      tuple[Path, ...]: The patched spec, then the generated modules.
  """
  return (PATCHED_SPEC, *sorted(GENERATED.glob("*.py")))


# -----------------------------------------------------------------------------
def checksums(paths: "tuple[Path, ...]") -> Dict[Path, Optional[str]]:
  """SHA-256 of each file, or None for a file that does not exist.

  Arguments:
      paths: The files to checksum.

  Returns:
      Dict[Path, Optional[str]]: The checksum of each path.
  """
  return {path: hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None for path in paths}


# -----------------------------------------------------------------------------
def detect() -> int:
  """Run upstream detection, then draft a changelog entry from its report.

  The draft is written here rather than in ``update`` because detect moves
  the lock file: a draft skipped on this run would never be offered again.

  Returns:
      int: detect's own exit code, which follows the same contract.
  """
  command = [sys.executable, str(ROOT / "upstream" / "detect.py")]
  code = subprocess.run(command, cwd=ROOT, check=False).returncode  # noqa: S603 - fixed arguments. # nosec B603
  if code != ERROR:
    draft_changelog()

  return code


# -----------------------------------------------------------------------------
def build_steps() -> None:
  """Patch the spec, generate the package, and format the result.

  Raises:
      StageError: When a step fails.
  """
  steps = [
    ("patch the spec", [sys.executable,
                        str(ROOT / "upstream" / "spec_fixes.py"), "apply", "--out",
                        relative(PATCHED_SPEC)]),
    ("generate the package", [sys.executable, str(ROOT / "codegen" / "generate.py")]),
  ]

  for name, args in steps:
    result = run_tool(args)
    if result.returncode != 0:
      # The tools print their reason on stderr, after any progress output.
      reason = (result.stderr.strip() or result.stdout.strip() or "no output").splitlines()[0]
      raise StageError(f"could not {name} (exit {result.returncode}): {reason}\n{result.stdout}{result.stderr}")

  pre_commit = shutil.which("pre-commit")
  if not pre_commit:
    raise StageError("pre-commit is not on PATH; it formats the generated files")

  # Only the formatters: the fix config also runs poetry lock on every
  # invocation, which would reach the network and rewrite poetry.lock.
  files = [*map(relative, build_outputs())]
  passes = [[
    run_tool([pre_commit, "run", hook, "--config", ".pre-commit-config-fix.yaml", "--files", *files]) for hook in FORMAT_HOOKS
  ] for _ in range(2)]

  # A fixing hook exits 1 when it changed a file, so the second pass is the
  # one that must come back clean.
  failed = [result for result in passes[1] if result.returncode != 0]
  if failed:
    raise StageError(f"pre-commit could not format the generated files:\n{failed[0].stdout}{failed[0].stderr}")


# -----------------------------------------------------------------------------
def build() -> int:
  """Regenerate the patched spec and the generated package.

  Returns:
      int: 0 when nothing changed, 2 when a file was regenerated, 1 on error.
  """
  before = checksums(build_outputs())

  try:
    build_steps()

  except StageError as exc:
    set_report_section("Regenerated", [f"Build failed: {str(exc).splitlines()[0]}"], "")
    print(f"build: error: {exc}", file=sys.stderr)
    return ERROR

  after = checksums(build_outputs())
  changed = [relative(path) for path in sorted({*before, *after}) if before.get(path) != after.get(path)]

  set_report_section("Regenerated", [f"`{path}`" for path in changed], "Nothing; the generated files were already current.")
  print(f"build: regenerated {', '.join(changed)}" if changed else "build: nothing to regenerate")
  return CHANGE if changed else NO_CHANGE


# -----------------------------------------------------------------------------
def check() -> int:
  """Run the test suite.

  Returns:
      int: 0 when every test passes, 2 when some fail, 1 when pytest itself
      could not run the suite.
  """
  # -rfE lists errors (a broken fixture, say) as well as failures.
  result = run_tool([sys.executable, "-m", "pytest", "-q", "-rfE", "-p", "no:randomly"])
  print(result.stdout, end="")
  print(result.stderr, end="", file=sys.stderr)

  # pytest exits 1 for failing tests; 2-5 mean it could not run them.
  if result.returncode not in (0, 1):
    set_report_section("Work created", [f"The test suite could not run (pytest exit {result.returncode})."], "")
    return ERROR

  failed = [line.split(" ", 2)[:2] for line in result.stdout.splitlines() if line.startswith(("FAILED ", "ERROR "))]
  set_report_section(
    "Work created", [f"{'Failing' if kind == 'FAILED' else 'Erroring'} test: `{name}`" for kind, name in failed],
    "None; every test passes."
  )
  return CHANGE if result.returncode == 1 else NO_CHANGE


# -----------------------------------------------------------------------------
def update() -> int:
  """Run detect, build and check in order.

  Returns:
      int: 1 at the first stage error, otherwise 2 if any stage found work,
      otherwise 0.
  """
  outcome = NO_CHANGE

  for stage in (detect, build, check):
    code = stage()
    if code == ERROR:
      return ERROR

    outcome = max(outcome, code)

  return outcome


STAGES: Dict[str, Callable[[], int]] = {"detect": detect, "build": build, "check": check, "update": update}


# -----------------------------------------------------------------------------
def main(argv: List[str]) -> int:
  """Dispatch to a stage.

  Arguments:
      argv: The command-line arguments, without the program name.

  Returns:
      int: The stage's exit code, or 1 for a bad argument.
  """
  if len(argv) != 1 or argv[0] not in STAGES:
    print(f"usage: pipeline.py {{{','.join(STAGES)}}}", file=sys.stderr)
    return ERROR

  return STAGES[argv[0]]()


if __name__ == "__main__":
  sys.exit(main(sys.argv[1:]))
