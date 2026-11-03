#!/usr/bin/env python3

"""Cut a release: close the changelog's Unreleased section, bump, and tag.

Usage:

- ``python release.py prepare {patch,minor,major}``: on a clean working
  tree, move everything under ``## [Unreleased]`` in ``CHANGELOG.md`` to a
  new ``## [X.Y.Z] - YYYY-MM-DD`` section, leave an empty Unreleased above
  it, update the compare links at the foot of the file, then run
  ``bump2version`` so the changelog, the version bump and the ``vX.Y.Z``
  tag land in one commit. Nothing is pushed.
- ``python release.py notes X.Y.Z``: print the body of the ``## [X.Y.Z]``
  section, for the GitHub Release the release workflow creates.

Both refuse, with exit 1 and the reason on stderr, while a changelog draft
from the update pipeline is still in the file (its ``<!-- draft`` comments
are the sign it has not been edited), and when the section they would
release is empty. ``prepare`` also refuses a dirty working tree and a
version the changelog or a tag already has. The format is Keep a Changelog's.
"""

import argparse
import datetime
from pathlib import Path
import re
import subprocess  # noqa: S404 - runs git and bump2version with fixed arguments. # nosec B404
import sys
from typing import List, Optional

ROOT = Path(__file__).resolve().parent
CHANGELOG = ROOT / "CHANGELOG.md"

# Must match tag_name in .bumpversion.cfg.
TAG_PREFIX = "v"

DRAFT = re.compile(r"<!-- (?:end )?draft ")
UNRELEASED = re.compile(r"^## \[Unreleased\][^\n]*\n", re.MULTILINE)

# A section runs to the next level-two heading or the link references at
# the foot of the file, whichever comes first.
SECTION_END = re.compile(r"^(?:## |\[[^\]\n]+\]: )", re.MULTILINE)
UNRELEASED_LINK = re.compile(r"^\[Unreleased\]: (?P<base>\S+)/compare/(?P<previous>\S+)\.\.\.HEAD$", re.MULTILINE)


class ReleaseError(Exception):
  """The release cannot go ahead; the message says why."""


# -----------------------------------------------------------------------------
def section_body(text: str, start: int) -> str:
  """Return the text of a section, from just below its heading to its end.

  Arguments:
      text: The changelog.
      start: The offset just past the section's heading line.

  Returns:
      str: The section's body, unstripped.
  """
  end = SECTION_END.search(text, start)
  return text[start:end.start() if end else len(text)]


# -----------------------------------------------------------------------------
def refuse_drafts(text: str) -> None:
  """Refuse while an update-pipeline draft is still in the changelog.

  Arguments:
      text: The changelog, or the part of it being released.

  Raises:
      ReleaseError: When a ``draft`` comment is present.
  """
  if DRAFT.search(text):
    raise ReleaseError(
      "the changelog still holds a draft from the update pipeline: edit its bullets, "
      "move them under the right heading, and delete both draft comments"
    )


# -----------------------------------------------------------------------------
def cut_changelog(text: str, version: str, date: str) -> str:
  """Move the Unreleased entries under a heading for ``version``.

  Leaves an empty ``## [Unreleased]`` above the new section. When the file
  ends with an ``[Unreleased]: <base>/compare/<previous>...HEAD`` link, it
  becomes a compare from the new tag, and a link for the new version is
  added below it; a file without one keeps its links as they are.

  Arguments:
      text: The changelog.
      version: The version being released, without the tag prefix.
      date: The release date, ``YYYY-MM-DD``.

  Returns:
      str: The changelog with the release cut.

  Raises:
      ReleaseError: When there is no Unreleased section, it is empty, a
      draft is still in the file, or ``version`` already has a section.
  """
  heading = UNRELEASED.search(text)

  if heading is None:
    raise ReleaseError("the changelog has no `## [Unreleased]` heading")

  if re.search(rf"^## \[{re.escape(version)}\]", text, re.MULTILINE):
    raise ReleaseError(f"the changelog already has a section for {version}")

  refuse_drafts(text)

  body = section_body(text, heading.end())

  if not body.strip():
    raise ReleaseError("nothing to release: `## [Unreleased]` is empty")

  rest = text[heading.end() + len(body):]
  released = f"## [{version}] - {date}\n\n{body.strip(chr(10))}\n"
  text = f"{text[:heading.end()]}\n{released}{chr(10) if rest else ''}{rest}"

  tag = f"{TAG_PREFIX}{version}"

  return UNRELEASED_LINK.sub(
    lambda link: f"[Unreleased]: {link['base']}/compare/{tag}...HEAD\n"
    f"[{version}]: {link['base']}/compare/{link['previous']}...{tag}", text
  )


# -----------------------------------------------------------------------------
def release_notes(text: str, version: str) -> str:
  """Return the body of the changelog section for ``version``.

  Arguments:
      text: The changelog.
      version: The released version, without the tag prefix.

  Returns:
      str: The section's body, stripped, ending in a newline.

  Raises:
      ReleaseError: When the section is missing or empty, or holds a draft.
  """
  heading = re.search(rf"^## \[{re.escape(version)}\][^\n]*\n", text, re.MULTILINE)

  if heading is None:
    raise ReleaseError(f"the changelog has no `## [{version}]` section")

  body = section_body(text, heading.end())
  refuse_drafts(body)

  if not body.strip():
    raise ReleaseError(f"the changelog's `## [{version}]` section is empty")

  return body.strip("\n") + "\n"


# -----------------------------------------------------------------------------
def run(args: List[str]) -> "subprocess.CompletedProcess[str]":
  """Run a command from the repository root, capturing its output.

  Arguments:
      args: The command and its arguments.

  Returns:
      subprocess.CompletedProcess[str]: The finished process.
  """
  return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=False)  # noqa: S603 - fixed arguments. # nosec B603


# -----------------------------------------------------------------------------
def bump(part: str, *flags: str) -> "subprocess.CompletedProcess[str]":
  """Run bump2version on ``part`` with extra flags.

  Arguments:
      part: ``patch``, ``minor`` or ``major``.
      flags: Further bump2version options.

  Returns:
      subprocess.CompletedProcess[str]: The finished process.
  """
  return run([sys.executable, "-m", "bumpversion", *flags, part])


# -----------------------------------------------------------------------------
def prepare(part: str, today: str) -> str:
  """Cut the changelog for the next ``part`` version, then bump and tag.

  Arguments:
      part: ``patch``, ``minor`` or ``major``.
      today: The release date, ``YYYY-MM-DD``.

  Returns:
      str: The new version.

  Raises:
      ReleaseError: When the tree is dirty, the tag exists, the changelog
      refuses, or bump2version fails. A bump that fails before committing
      leaves the tree as it was.
  """
  status = run(["git", "status", "--porcelain"])

  if status.returncode != 0 or status.stdout.strip():
    raise ReleaseError("the working tree must be clean: commit or stash first")

  listed = bump(part, "--dry-run", "--list")
  version = re.search(r"^new_version=(\S+)$", listed.stdout, re.MULTILINE)

  if listed.returncode != 0 or version is None:
    raise ReleaseError(f"bump2version could not work out the next {part} version:\n{listed.stderr}")

  tag = f"{TAG_PREFIX}{version[1]}"

  if run(["git", "rev-parse", "--quiet", "--verify", f"refs/tags/{tag}"]).returncode == 0:
    raise ReleaseError(f"tag {tag} already exists")

  CHANGELOG.write_text(cut_changelog(CHANGELOG.read_text(encoding="utf-8"), version[1], today), encoding="utf-8")
  head = run(["git", "rev-parse", "HEAD"]).stdout

  # bump2version stages only the files it edits, then commits the index, so
  # the staged changelog rides in the same commit as the bump.
  run(["git", "add", CHANGELOG.name])
  bumped = bump(part, "--allow-dirty")

  if bumped.returncode == 0:
    return version[1]

  if run(["git", "rev-parse", "HEAD"]).stdout != head:
    raise ReleaseError(f"bump2version committed but did not finish; check the commit and tag {tag}:\n{bumped.stderr}")

  # The tree was clean before, so every tracked change is this run's.
  run(["git", "restore", "--staged", "--worktree", "--", "."])
  raise ReleaseError(f"bump2version failed; the working tree is restored:\n{bumped.stderr}")


# -----------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
  """Run a subcommand.

  Arguments:
      argv: The command-line arguments, without the program name.

  Returns:
      int: 0 on success, 1 when the release is refused.
  """
  parser = argparse.ArgumentParser(description="Cut a release of bw-serve-client.")
  commands = parser.add_subparsers(dest="command", required=True)
  prepare_parser = commands.add_parser("prepare", help="cut the changelog, bump the version and tag it")
  prepare_parser.add_argument("part", choices=["patch", "minor", "major"])
  notes_parser = commands.add_parser("notes", help="print a released version's changelog section")
  notes_parser.add_argument("version")
  args = parser.parse_args(argv)

  try:
    if args.command == "notes":
      print(release_notes(CHANGELOG.read_text(encoding="utf-8"), args.version), end="")

    else:
      today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
      version = prepare(args.part, today)
      tag = f"{TAG_PREFIX}{version}"
      print(f"release: committed and tagged {tag}. Push both to publish it:\n  git push origin master {tag}")

  except ReleaseError as exc:
    print(f"release: refused: {exc}", file=sys.stderr)
    return 1

  return 0


if __name__ == "__main__":
  sys.exit(main())
