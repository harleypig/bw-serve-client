"""Tests for the release step (release.py, #52).

``prepare`` closes the changelog's Unreleased section and bumps the
version in one commit; ``notes`` reads a released section back out for
the GitHub Release. Both must refuse while an update-pipeline draft is
still in the changelog.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import List

from _loader import load_tool
import pytest

release = load_tool("release.py", "_bw_test_release_release")

BASE = "https://github.com/harleypig/bw-serve-client"

CHANGELOG = f"""# Changelog

The format is based on [Keep a Changelog][kac].

## [Unreleased]

### Added

- Something new.

### Fixed

- Something broken.

## [0.1.0] - 2026-01-01

- Older.

[kac]: https://keepachangelog.com/en/1.1.0/
[Unreleased]: {BASE}/compare/v0.1.0...HEAD
[0.1.0]: {BASE}/compare/0.0.4a0...v0.1.0
"""

DRAFT = """<!-- draft 0123456789ab: written by the update pipeline from the change report.
Edit these, move them under Added, Changed or Fixed, then delete both
draft comments. -->

- Upstream `cli`: a → b

<!-- end draft 0123456789ab -->
"""


class TestCutChangelog:
  """Cutting the changelog moves Unreleased under a version heading."""

  def test_moves_entries_and_leaves_an_empty_unreleased(self: TestCutChangelog) -> None:
    """The entries move intact and Unreleased is left empty above them."""
    text = release.cut_changelog(CHANGELOG, "0.2.0", "2026-11-03")

    assert "## [Unreleased]\n\n## [0.2.0] - 2026-11-03\n\n### Added\n\n- Something new.\n" in text
    assert "- Something broken.\n\n## [0.1.0] - 2026-01-01\n" in text
    assert text.count("- Something new.") == 1

  def test_rewrites_the_compare_links(self: TestCutChangelog) -> None:
    """Unreleased compares from the new tag; the new version gets a link."""
    text = release.cut_changelog(CHANGELOG, "0.2.0", "2026-11-03")

    assert f"[Unreleased]: {BASE}/compare/v0.2.0...HEAD\n[0.2.0]: {BASE}/compare/v0.1.0...v0.2.0\n" in text
    assert f"[0.1.0]: {BASE}/compare/0.0.4a0...v0.1.0\n" in text

  def test_first_release_ends_at_the_links(self: TestCutChangelog) -> None:
    """With no earlier version, the section ends at the link references."""
    first = CHANGELOG.replace("## [0.1.0] - 2026-01-01\n\n- Older.\n\n", "")
    text = release.cut_changelog(first, "0.1.1", "2026-11-03")

    assert "- Something broken.\n\n[kac]: " in text

  def test_no_unreleased_link_leaves_links_alone(self: TestCutChangelog) -> None:
    """A changelog without an Unreleased compare link keeps its links."""
    bare = CHANGELOG.replace(f"[Unreleased]: {BASE}/compare/v0.1.0...HEAD\n", "")
    text = release.cut_changelog(bare, "0.2.0", "2026-11-03")

    assert "[0.2.0]:" not in text
    assert text.endswith(f"[0.1.0]: {BASE}/compare/0.0.4a0...v0.1.0\n")

  def test_refuses_while_a_draft_is_present(self: TestCutChangelog) -> None:
    """An unedited update-pipeline draft blocks the release."""
    drafted = CHANGELOG.replace("## [Unreleased]\n", f"## [Unreleased]\n\n{DRAFT}")

    with pytest.raises(release.ReleaseError, match="draft"):
      release.cut_changelog(drafted, "0.2.0", "2026-11-03")

  def test_refuses_a_lone_end_marker(self: TestCutChangelog) -> None:
    """Deleting only the opening draft comment is still a draft."""
    drafted = CHANGELOG.replace("- Something new.\n", "- Something new.\n\n<!-- end draft 0123456789ab -->\n")

    with pytest.raises(release.ReleaseError, match="draft"):
      release.cut_changelog(drafted, "0.2.0", "2026-11-03")

  @pytest.mark.parametrize("body", ["", "\n\n   \n"])
  def test_refuses_an_empty_unreleased(self: TestCutChangelog, body: str) -> None:
    """Nothing under Unreleased means nothing to release."""
    start = CHANGELOG.index("### Added")
    end = CHANGELOG.index("## [0.1.0]")
    empty = f"{CHANGELOG[:start]}{body}{CHANGELOG[end:]}"

    with pytest.raises(release.ReleaseError, match="empty"):
      release.cut_changelog(empty, "0.2.0", "2026-11-03")

  def test_refuses_without_an_unreleased_heading(self: TestCutChangelog) -> None:
    """A changelog with no Unreleased heading cannot be cut."""
    with pytest.raises(release.ReleaseError, match="no `## \\[Unreleased\\]`"):
      release.cut_changelog(CHANGELOG.replace("## [Unreleased]\n", ""), "0.2.0", "2026-11-03")

  def test_refuses_a_version_already_released(self: TestCutChangelog) -> None:
    """A version that already has a section is not released twice."""
    with pytest.raises(release.ReleaseError, match="already has a section for 0.1.0"):
      release.cut_changelog(CHANGELOG, "0.1.0", "2026-11-03")


class TestReleaseNotes:
  """The release notes are one version's section back out."""

  def test_returns_the_section_body(self: TestReleaseNotes) -> None:
    """The notes are the section's body, without its heading or the next."""
    text = release.cut_changelog(CHANGELOG, "0.2.0", "2026-11-03")

    assert release.release_notes(text, "0.2.0") == "### Added\n\n- Something new.\n\n### Fixed\n\n- Something broken.\n"

  def test_last_section_stops_at_the_links(self: TestReleaseNotes) -> None:
    """The oldest section ends before the link references."""
    assert release.release_notes(CHANGELOG, "0.1.0") == "- Older.\n"

  def test_refuses_a_missing_section(self: TestReleaseNotes) -> None:
    """A version the changelog does not have gives no notes."""
    with pytest.raises(release.ReleaseError, match="no `## \\[9.9.9\\]` section"):
      release.release_notes(CHANGELOG, "9.9.9")

  def test_refuses_a_draft_in_the_section(self: TestReleaseNotes) -> None:
    """A draft that reached a released section blocks the notes."""
    drafted = CHANGELOG.replace("- Older.\n", f"- Older.\n\n{DRAFT}")

    with pytest.raises(release.ReleaseError, match="draft"):
      release.release_notes(drafted, "0.1.0")

  def test_refuses_an_empty_section(self: TestReleaseNotes) -> None:
    """A heading with nothing under it gives no notes."""
    with pytest.raises(release.ReleaseError, match="empty"):
      release.release_notes(CHANGELOG.replace("- Older.\n\n", ""), "0.1.0")


class TestMain:
  """The command line reports refusals as exit 1."""

  def test_notes_prints_the_section(
    self: TestMain, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
  ) -> None:
    """``notes X.Y.Z`` prints the section and exits 0."""
    path = tmp_path / "CHANGELOG.md"
    path.write_text(CHANGELOG, encoding="utf-8")
    monkeypatch.setattr(release, "CHANGELOG", path)

    assert release.main(["notes", "0.1.0"]) == 0
    assert capsys.readouterr().out == "- Older.\n"

  def test_notes_refusal_exits_1(
    self: TestMain, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
  ) -> None:
    """A missing section is a refusal on stderr and exit 1."""
    path = tmp_path / "CHANGELOG.md"
    path.write_text(CHANGELOG, encoding="utf-8")
    monkeypatch.setattr(release, "CHANGELOG", path)

    assert release.main(["notes", "9.9.9"]) == 1
    assert "release: refused:" in capsys.readouterr().err


# -----------------------------------------------------------------------------
def git(repo: Path, *args: str) -> str:
  """Run git in ``repo`` and return its output.

  Arguments:
      repo: The repository.
      args: The git arguments.

  Returns:
      str: Standard output, stripped.
  """
  return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
  """Make a throwaway git repository with this repo's bump2version setup.

  Holds a copy of ``.bumpversion.cfg``, the two files it edits at the
  version it names, and the test changelog, all committed.
  """
  root = Path(release.ROOT)
  shutil.copy(root / ".bumpversion.cfg", tmp_path)
  current = next(
    line.split("=", 1)[1].strip()
    for line in (root / ".bumpversion.cfg").read_text().splitlines()
    if line.startswith("current_version")
  )
  (tmp_path / "pyproject.toml").write_text(f"[project]\nversion = {json.dumps(current)}\n", encoding="utf-8")
  (tmp_path / "bw_serve_client").mkdir()
  (tmp_path / "bw_serve_client" / "__init__.py").write_text(f"__version__ = {json.dumps(current)}\n", encoding="utf-8")
  (tmp_path / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")

  git(tmp_path, "init", "-q")
  git(tmp_path, "config", "user.email", "test@example.com")
  git(tmp_path, "config", "user.name", "Test")
  git(tmp_path, "config", "commit.gpgsign", "false")
  git(tmp_path, "config", "tag.gpgsign", "false")
  git(tmp_path, "add", ".")
  git(tmp_path, "commit", "-q", "-m", "seed")

  monkeypatch.setattr(release, "ROOT", tmp_path)
  monkeypatch.setattr(release, "CHANGELOG", tmp_path / "CHANGELOG.md")
  return tmp_path


def next_patch(repo: Path) -> List[str]:
  """Return the current version and the patch after it, from the config.

  Arguments:
      repo: The repository.

  Returns:
      List[str]: ``[current, next]``.
  """
  listed = subprocess.run([sys.executable, "-m", "bumpversion", "--dry-run", "--list", "patch"],
                          cwd=repo,
                          capture_output=True,
                          text=True,
                          check=True).stdout
  values = dict(line.split("=", 1) for line in listed.splitlines() if "=" in line)
  return [values["current_version"], values["new_version"]]


class TestPrepare:
  """Preparing cuts the changelog and bumps in a single commit and tag."""

  def test_commits_changelog_and_bump_together(self: TestPrepare, repo: Path) -> None:
    """One commit carries the changelog and the version; the tag is on it."""
    current, new = next_patch(repo)

    assert release.prepare("patch", "2026-11-03") == new

    assert git(repo, "status", "--porcelain") == ""
    assert sorted(git(repo, "show", "--name-only", "--format=", "HEAD").splitlines()) == [
      ".bumpversion.cfg", "CHANGELOG.md", "bw_serve_client/__init__.py", "pyproject.toml"
    ]
    assert git(repo, "tag", "--points-at", "HEAD") == f"v{new}"
    assert f"## [{new}] - 2026-11-03" in (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"__version__ = {json.dumps(new)}" in (repo / "bw_serve_client" / "__init__.py").read_text(encoding="utf-8")
    assert current != new

  def test_refuses_a_dirty_tree(self: TestPrepare, repo: Path) -> None:
    """Uncommitted work stops the release before anything is touched."""
    (repo / "stray.txt").write_text("x", encoding="utf-8")

    with pytest.raises(release.ReleaseError, match="clean"):
      release.prepare("patch", "2026-11-03")

    assert git(repo, "tag") == ""

  def test_draft_refusal_changes_nothing(self: TestPrepare, repo: Path) -> None:
    """A draft in the changelog stops the release with no commit or tag."""
    drafted = CHANGELOG.replace("## [Unreleased]\n", f"## [Unreleased]\n\n{DRAFT}")
    (repo / "CHANGELOG.md").write_text(drafted, encoding="utf-8")
    git(repo, "commit", "-q", "-am", "draft")
    head = git(repo, "rev-parse", "HEAD")

    with pytest.raises(release.ReleaseError, match="draft"):
      release.prepare("patch", "2026-11-03")

    assert git(repo, "rev-parse", "HEAD") == head
    assert git(repo, "tag") == ""
    assert git(repo, "status", "--porcelain") == ""

  def test_refuses_an_existing_tag(self: TestPrepare, repo: Path) -> None:
    """A tag already holding the next version stops the release."""
    _, new = next_patch(repo)
    git(repo, "tag", f"v{new}")

    with pytest.raises(release.ReleaseError, match="already exists"):
      release.prepare("patch", "2026-11-03")

    assert git(repo, "status", "--porcelain") == ""

  def test_failed_bump_restores_the_tree(self: TestPrepare, repo: Path) -> None:
    """When the bump commit fails, every file goes back as it was."""
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    hook.chmod(0o755)
    head = git(repo, "rev-parse", "HEAD")

    with pytest.raises(release.ReleaseError, match="restored"):
      release.prepare("patch", "2026-11-03")

    assert git(repo, "rev-parse", "HEAD") == head
    assert git(repo, "status", "--porcelain") == ""
    assert (repo / "CHANGELOG.md").read_text(encoding="utf-8") == CHANGELOG
