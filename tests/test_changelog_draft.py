"""The changelog draft, built from detect's data rather than its report (#117).

``upstream/detect.py --draft-data PATH`` writes the changed sources, spec
changes and route changes as JSON; ``pipeline.py`` drafts the changelog
entry from that file, so the change report's layout can change without the
draft silently going empty.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from _loader import load_tool
import pytest

if TYPE_CHECKING:
  from pytest_mock import MockerFixture

PIN = "cli-v2026.11.0"

detect = load_tool("upstream/detect.py", "_bw_test_changelog_draft_detect")
pipeline = load_tool("pipeline.py", "_bw_test_changelog_draft_pipeline")

CHANGELOG_SEED = """# Changelog

## [Unreleased]

### Added

- Something a person wrote.

## [0.1.0] - 2026-01-01

- Older.
"""


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
  """Point every file detect and the draft read or write into tmp_path."""
  for name, filename in (
    ("SPEC_SNAPSHOT", "vault-management-api-original.json"),
    ("ROUTES_SNAPSHOT", "serve-routes.txt"),
    ("LOCK_FILE", "lock.json"),
    ("WATCH_FILE", "watch.json"),
    ("FIXES_FILE", "spec-fixes.json"),
    ("DECISIONS_FILE", "route-decisions.json"),
  ):
    monkeypatch.setattr(detect, name, tmp_path / filename)

  (tmp_path / "spec-fixes.json").write_text(json.dumps({"fixes": []}), encoding="utf-8")
  (tmp_path / "serve").mkdir()
  monkeypatch.setattr(detect, "SERVE_FIXTURES_DIR", tmp_path / "serve")

  (tmp_path / "CHANGELOG.md").write_text(CHANGELOG_SEED, encoding="utf-8")
  monkeypatch.setattr(pipeline, "REPORT", tmp_path / "change-report.md")
  monkeypatch.setattr(pipeline, "CHANGELOG", tmp_path / "CHANGELOG.md")
  return tmp_path


def run(
  repo: Path,
  monkeypatch: pytest.MonkeyPatch,
  release: str = PIN,
  package: str = "2.0.0",
  state: str = "open",
  routes: Optional[List[str]] = None,
  draft: bool = True,
) -> int:
  """Run detection once against a fixed upstream.

  Arguments:
    repo: The temporary directory.
    monkeypatch: Replaces the fetch with the given upstream.
    release: The CLI release upstream has.
    package: The watched PyPI package's version.
    state: The watched issue's state.
    routes: The route lines bw serve registers.
    draft: Whether to ask for the draft data.

  Returns:
    detect's exit code.
  """
  upstream = detect.Upstream({"paths": {}}, release, {}, routes or [], {"bitwarden/clients#1": state}, {"bitwarden-sdk": package})
  monkeypatch.setattr(detect, "fetch_all", lambda session, watch: upstream)  # noqa: U100 - matches fetch_all's signature.

  return detect.run(None, repo / "change-report.md", "2026-11-03", repo / "draft.json" if draft else None)


def unreleased(repo: Path) -> str:
  """Return what sits under ``## [Unreleased]``, up to the next heading.

  Arguments:
    repo: The temporary directory.

  Returns:
    The section's body.
  """
  text = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
  return text.split("## [Unreleased]\n", 1)[1].split("\n### ", 1)[0]


def draft_data(sources: List[List[str]], spec: List[str], routes: List[str]) -> Dict[str, Any]:
  """Build draft data the way detect writes it.

  Arguments:
    sources: ``[source, was, now]`` for each changed source.
    spec: The spec change bullets.
    routes: The route change bullets.

  Returns:
    The data.
  """
  return {"sources": [{"source": s, "was": w, "now": n} for s, w, n in sources], "spec": spec, "routes": routes}


CHANGED = draft_data([["cli", "2026.10.1", "2026.11.0"]], ["Route added: `GET /new`"], ["Added: `GET /new`"])


def write(repo: Path, data: Dict[str, Any]) -> Path:
  """Write draft data and a report for the outcome to land in.

  Arguments:
    repo: The temporary directory.
    data: The draft data.

  Returns:
    The data file.
  """
  (repo / "change-report.md").write_text("# Upstream change report\n", encoding="utf-8")
  path = repo / "draft.json"
  path.write_text(json.dumps(data), encoding="utf-8")
  return path


class TestFromDetect:
  """A real detect run handing its changes to the draft."""

  def test_table_layout_change_still_drafts(self: TestFromDetect, repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A sources table rendered differently leaves the draft intact.

    The table gains a column and loses its padding; a draft parsed from the
    report would find no rows and write nothing.
    """
    render = detect.render_report

    def reshaped(changes: Any, lock: Dict[str, Any]) -> str:
      text = render(changes, lock)
      return re.sub(r"^\| (.*) \|$", lambda m: "|" + m.group(1).replace(" | ", "|") + "|extra|", text, flags=re.MULTILINE)

    monkeypatch.setattr(detect, "render_report", reshaped)
    run(repo, monkeypatch, release="cli-v2026.10.1")

    code = run(repo, monkeypatch, routes=["GET /status  oss"])
    pipeline.draft_changelog(repo / "draft.json")

    report = (repo / "change-report.md").read_text(encoding="utf-8")
    assert code == 2
    assert "|cli|cli-v2026.10.1|cli-v2026.11.0|extra|" in report
    assert "| cli |" not in report
    draft = unreleased(repo)
    assert "- Upstream `cli`: cli-v2026.10.1 → cli-v2026.11.0" in draft
    assert "- bw serve routes: Added: `GET /status  oss`" in draft
    assert "Drafted an entry" in report

  def test_watched_items_appear_once(self: TestFromDetect, repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A watched package and a watched issue each give one bullet."""
    run(repo, monkeypatch)

    run(repo, monkeypatch, package="2.1.0", state="closed")
    pipeline.draft_changelog(repo / "draft.json")

    draft = unreleased(repo)
    assert draft.count("bitwarden-sdk") == 1
    assert "- Upstream `packages bitwarden-sdk`: 2.0.0 → 2.1.0" in draft
    assert draft.count("bitwarden/clients#1") == 1

  def test_no_change_writes_empty_sources(self: TestFromDetect, repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An unchanged run still writes the data, with nothing to draft."""
    run(repo, monkeypatch)

    run(repo, monkeypatch)
    pipeline.draft_changelog(repo / "draft.json")

    assert json.loads((repo / "draft.json").read_text(encoding="utf-8"))["sources"] == []
    assert (repo / "CHANGELOG.md").read_text(encoding="utf-8") == CHANGELOG_SEED

  def test_no_data_unless_asked(self: TestFromDetect, repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Without --draft-data detect writes no data file."""
    run(repo, monkeypatch, draft=False)

    assert not (repo / "draft.json").exists()

  def test_failed_run_writes_no_data(self: TestFromDetect, repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A failed fetch leaves no data behind to draft from."""

    def broken(session: Any, watch: Any) -> Any:  # noqa: U100 - matches fetch_all's signature.
      raise detect.FetchError("no spec")

    monkeypatch.setattr(detect, "fetch_all", broken)

    code = detect.run(None, repo / "change-report.md", "2026-11-03", repo / "draft.json")

    assert code == 1
    assert not (repo / "draft.json").exists()

  def test_main_takes_draft_data(self: TestFromDetect, mocker: MockerFixture, tmp_path: Path) -> None:
    """The command line passes --draft-data through to the run."""
    runner = mocker.patch.object(detect, "run", return_value=0)

    assert detect.main(["--draft-data", str(tmp_path / "d.json")]) == 0
    assert runner.call_args.args[3] == tmp_path / "d.json"


class TestDraftChangelog:
  """Writing the draft into the changelog."""

  def test_draft_added_on_change(self: TestDraftChangelog, repo: Path) -> None:
    """A changed source puts a marked draft directly under Unreleased."""
    pipeline.draft_changelog(write(repo, CHANGED))

    block = unreleased(repo).strip()
    assert block.startswith("<!-- draft ")
    assert block.endswith(" -->")
    assert "<!-- end draft " in block
    assert "- Upstream `cli`: 2026.10.1 → 2026.11.0" in block
    assert "- Upstream spec: Route added: `GET /new`" in block
    assert "- bw serve routes: Added: `GET /new`" in block
    assert "Drafted an entry" in (repo / "change-report.md").read_text(encoding="utf-8")

  def test_human_entries_untouched(self: TestDraftChangelog, repo: Path) -> None:
    """Removing the inserted block gives back the file exactly as it was."""
    pipeline.draft_changelog(write(repo, CHANGED))

    text = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    start, end = text.index("<!-- draft "), text.index("<!-- end draft ")
    end = text.index("-->", end) + len("-->\n\n")
    assert text[:start] + text[end:] == CHANGELOG_SEED

  def test_idempotent_on_rerun(self: TestDraftChangelog, repo: Path) -> None:
    """A second run on the same changes adds nothing."""
    path = write(repo, CHANGED)
    pipeline.draft_changelog(path)
    once = (repo / "CHANGELOG.md").read_text(encoding="utf-8")

    pipeline.draft_changelog(path)

    assert (repo / "CHANGELOG.md").read_text(encoding="utf-8") == once
    assert "Already drafted" in (repo / "change-report.md").read_text(encoding="utf-8")

  def test_no_draft_without_changed_source(self: TestDraftChangelog, repo: Path) -> None:
    """Spec or route bullets alone, with no changed source, draft nothing."""
    pipeline.draft_changelog(write(repo, draft_data([], ["Route added: `GET /new`"], [])))

    assert (repo / "CHANGELOG.md").read_text(encoding="utf-8") == CHANGELOG_SEED
    assert (repo / "change-report.md").read_text(encoding="utf-8") == "# Upstream change report\n"

  def test_no_draft_without_data(self: TestDraftChangelog, repo: Path) -> None:
    """No data file, nothing to draft from."""
    pipeline.draft_changelog(repo / "draft.json")

    assert (repo / "CHANGELOG.md").read_text(encoding="utf-8") == CHANGELOG_SEED

  def test_missing_changelog(self: TestDraftChangelog, repo: Path) -> None:
    """A missing changelog is not created; the report says why."""
    (repo / "CHANGELOG.md").unlink()

    pipeline.draft_changelog(write(repo, CHANGED))

    assert not (repo / "CHANGELOG.md").exists()
    assert "No draft: `CHANGELOG.md` is missing." in (repo / "change-report.md").read_text(encoding="utf-8")

  def test_changelog_without_unreleased(self: TestDraftChangelog, repo: Path) -> None:
    """A changelog with no Unreleased heading is left alone; the report says why."""
    (repo / "CHANGELOG.md").write_text("# Changelog\n\n## [0.1.0]\n", encoding="utf-8")

    pipeline.draft_changelog(write(repo, CHANGED))

    assert (repo / "CHANGELOG.md").read_text(encoding="utf-8") == "# Changelog\n\n## [0.1.0]\n"
    assert "has no `## [Unreleased]` heading" in (repo / "change-report.md").read_text(encoding="utf-8")


class TestPipelineDetect:
  """The detect stage asking for the data and drafting from it."""

  @pytest.mark.parametrize(("code", "drafted"), [(0, False), (2, True), (1, False), (-9, False)])
  def test_drafts_only_on_change(self: TestPipelineDetect, mocker: MockerFixture, code: int, drafted: bool) -> None:
    """Detect drafts only after a run that reported a change, keeping its exit code."""
    process = mocker.patch.object(pipeline.subprocess, "run")
    process.return_value.returncode = code
    draft = mocker.patch.object(pipeline, "draft_changelog")

    assert pipeline.detect() == code
    assert draft.called is drafted

    command = process.call_args.args[0]
    assert command[-2] == "--draft-data"
    if drafted:
      assert draft.call_args.args[0] == Path(command[-1])

  def test_data_does_not_outlive_the_stage(self: TestPipelineDetect, mocker: MockerFixture) -> None:
    """The data file is temporary, so no later run can draft from it."""
    seen: List[Path] = []

    def detect_run(command: List[str], **_: Any) -> Any:  # noqa: U101 - takes subprocess.run's keyword arguments.
      Path(command[-1]).write_text(json.dumps(CHANGED), encoding="utf-8")
      return mocker.Mock(returncode=2)

    mocker.patch.object(pipeline.subprocess, "run", side_effect=detect_run)
    mocker.patch.object(pipeline, "draft_changelog", side_effect=lambda path: seen.append(path) or None)

    pipeline.detect()

    assert len(seen) == 1
    assert not seen[0].exists()
