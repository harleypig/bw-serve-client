"""Tests for the update pipeline's stages and exit-code contract (pipeline.py)."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from typing import List, TYPE_CHECKING

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "upstream"))

import detect  # noqa: E402 - importable only once upstream/ is on the path.

import pipeline  # noqa: E402 - importable only once the repository root is on the path.

if TYPE_CHECKING:
  from pytest_mock import MockerFixture


@pytest.fixture
def report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
  """Point the change report into a temporary directory."""
  path = tmp_path / "change-report.md"
  monkeypatch.setattr(pipeline, "REPORT", path)
  return path


def finished(code: int, stdout: str = "") -> subprocess.CompletedProcess[str]:
  """Build a finished process with the given exit code and output.

  Arguments:
      code: The exit code.
      stdout: The captured standard output.

  Returns:
      subprocess.CompletedProcess[str]: The process.
  """
  return subprocess.CompletedProcess([], code, stdout, "")


class TestReportSection:
  """Filling in one section of the change report."""

  def test_replaces_existing_section(self: TestReportSection, report: Path) -> None:
    """A section detect left a placeholder in is replaced in place."""
    report.write_text("# R\n\n## Regenerated\n\nNot run.\n\n## Work created\n\nNot run.\n", encoding="utf-8")

    pipeline.set_report_section("Regenerated", ["`a.py`"], "Nothing.")

    assert report.read_text(encoding="utf-8") == "# R\n\n## Regenerated\n\n- `a.py`\n\n## Work created\n\nNot run.\n"

  def test_replaces_last_section(self: TestReportSection, report: Path) -> None:
    """The final section is replaced without leaving stale lines."""
    report.write_text("# R\n\n## Work created\n\nNot run.\n", encoding="utf-8")

    pipeline.set_report_section("Work created", [], "None.")

    assert report.read_text(encoding="utf-8") == "# R\n\n## Work created\n\nNone.\n"

  def test_starts_a_report_when_missing(self: TestReportSection, report: Path) -> None:
    """A stage run alone still leaves its result on record."""
    pipeline.set_report_section("Work created", ["Failing test: `t`"], "None.")

    assert report.read_text(encoding="utf-8") == "# Upstream change report\n\n## Work created\n\n- Failing test: `t`\n"


class TestCheck:
  """Check: pytest's result mapped onto the contract."""

  @pytest.mark.usefixtures("report")
  @pytest.mark.parametrize(("pytest_code", "expected"), [(0, 0), (1, 2), (2, 1), (4, 1), (5, 1)])
  def test_exit_codes(self: TestCheck, mocker: MockerFixture, pytest_code: int, expected: int) -> None:
    """Passing is 0, failing tests are work (2), pytest trouble is an error (1)."""
    mocker.patch.object(pipeline, "run_tool", return_value=finished(pytest_code))

    assert pipeline.check() == expected

  def test_failing_tests_are_listed(self: TestCheck, report: Path, mocker: MockerFixture) -> None:
    """Each failing test lands in the report as work created."""
    output = "F.\nFAILED tests/test_x.py::test_a - AssertionError\n1 failed, 1 passed\n"
    mocker.patch.object(pipeline, "run_tool", return_value=finished(1, output))

    pipeline.check()

    assert "- Failing test: `tests/test_x.py::test_a`" in report.read_text(encoding="utf-8")

  def test_erroring_tests_are_listed(self: TestCheck, report: Path, mocker: MockerFixture) -> None:
    """A test that errors in setup is work too, never 'every test passes'."""
    output = "E\nERROR tests/test_x.py::test_b - RuntimeError\n1 error\n"
    mocker.patch.object(pipeline, "run_tool", return_value=finished(1, output))

    assert pipeline.check() == 2
    assert "- Erroring test: `tests/test_x.py::test_b`" in report.read_text(encoding="utf-8")


class TestBuild:
  """Build: regenerated files mapped onto the contract."""

  @pytest.fixture
  def outputs(self: TestBuild, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> List[Path]:
    """Two stand-in generated files inside a temporary root."""
    paths = [tmp_path / "fixed.json", tmp_path / "_generated" / "models.py"]
    paths[1].parent.mkdir()
    for path in paths:
      path.write_text("old\n", encoding="utf-8")

    monkeypatch.setattr(pipeline, "ROOT", tmp_path)
    monkeypatch.setattr(pipeline, "PATCHED_SPEC", paths[0])
    monkeypatch.setattr(pipeline, "GENERATED", paths[1].parent)
    return paths

  @pytest.mark.usefixtures("outputs")
  def test_unchanged_outputs_are_no_change(self: TestBuild, report: Path, mocker: MockerFixture) -> None:
    """A build that rewrites identical files exits 0."""
    mocker.patch.object(pipeline, "build_steps")

    assert pipeline.build() == 0
    assert "Nothing; the generated files were already current." in report.read_text(encoding="utf-8")

  def test_changed_output_is_a_change(self: TestBuild, report: Path, outputs: List[Path], mocker: MockerFixture) -> None:
    """A build that changes a file exits 2 and names it."""
    mocker.patch.object(pipeline, "build_steps", side_effect=lambda: outputs[1].write_text("new\n", encoding="utf-8"))

    assert pipeline.build() == 2
    assert "- `_generated/models.py`" in report.read_text(encoding="utf-8")

  @pytest.mark.usefixtures("outputs")
  def test_new_generated_module_is_a_change(self: TestBuild, report: Path, outputs: List[Path], mocker: MockerFixture) -> None:
    """A module the generator adds counts, though nothing lists it."""
    added = outputs[1].parent / "extra.py"
    mocker.patch.object(pipeline, "build_steps", side_effect=lambda: added.write_text("new\n", encoding="utf-8"))

    assert pipeline.build() == 2
    assert "- `_generated/extra.py`" in report.read_text(encoding="utf-8")

  def test_failed_step_is_an_error(self: TestBuild, report: Path, mocker: MockerFixture) -> None:
    """A failing step exits 1 and says which."""
    mocker.patch.object(
      pipeline, "build_steps", side_effect=pipeline.StageError("could not patch the spec (exit 2): boom\nfull output")
    )

    assert pipeline.build() == 1
    assert "Build failed: could not patch the spec (exit 2): boom" in report.read_text(encoding="utf-8")

  def test_step_failure_raises(self: TestBuild, mocker: MockerFixture) -> None:
    """Build_steps stops at the first failing tool."""
    mocker.patch.object(
      pipeline,
      "run_tool",
      return_value=subprocess.CompletedProcess([], 2, "Loading files...\n", "Error: Missing required field\n")
    )

    with pytest.raises(pipeline.StageError, match=r"could not patch the spec \(exit 2\): Error: Missing required field"):
      pipeline.build_steps()

  def test_missing_pre_commit_raises(self: TestBuild, mocker: MockerFixture) -> None:
    """Without pre-commit the generated files cannot be formatted."""
    mocker.patch.object(pipeline, "run_tool", return_value=finished(0))
    mocker.patch.object(pipeline.shutil, "which", return_value=None)

    with pytest.raises(pipeline.StageError, match="pre-commit is not on PATH"):
      pipeline.build_steps()

  def test_formatter_gets_a_second_pass(self: TestBuild, mocker: MockerFixture) -> None:
    """A first formatting pass that changed files is followed by a clean one."""
    hooks = len(pipeline.FORMAT_HOOKS)
    first_pass = [finished(1)] * hooks
    run_tool = mocker.patch.object(
      pipeline, "run_tool", side_effect=[finished(0), finished(0), *first_pass, *[finished(0)] * hooks]
    )
    mocker.patch.object(pipeline.shutil, "which", return_value="/usr/bin/pre-commit")

    pipeline.build_steps()

    assert run_tool.call_count == 2 + 2 * hooks
    assert {call.args[0][2] for call in run_tool.call_args_list[2:]} == set(pipeline.FORMAT_HOOKS)

  def test_formatter_that_never_settles_raises(self: TestBuild, mocker: MockerFixture) -> None:
    """Two failing formatting passes are an error."""
    hooks = len(pipeline.FORMAT_HOOKS)
    mocker.patch.object(pipeline, "run_tool", side_effect=[finished(0), finished(0), *[finished(0)] * (2 * hooks - 1), finished(1)])
    mocker.patch.object(pipeline.shutil, "which", return_value="/usr/bin/pre-commit")

    with pytest.raises(pipeline.StageError, match="could not format"):
      pipeline.build_steps()


CHANGELOG_SEED = """# Changelog

## [Unreleased]

### Added

- Something a person wrote.

## [0.1.0] - 2026-01-01

- Older.
"""


def change_report(changed: bool) -> str:
  """Render a change report the way detect writes one.

  Arguments:
      changed: Whether a recorded source changed.

  Returns:
      str: The report.
  """
  changes = detect.Changes(stale_fixes=["a fix"])
  if changed:
    changes.sources = [("cli", "2026.10.1", "2026.11.0"), ("spec", "aaaaaaaaaaaa", "bbbbbbbbbbbb")]
    changes.spec = ["Route added: `GET /new`"]
    changes.routes = ["Added: `GET /new`"]

  lock = {"cli": {"release": "2026.11.0"}, "spec": {"fetched": "2026-11-02"}}
  return detect.render_report(changes, lock)


class TestChangelogDraft:
  """Drafting a changelog entry from the change report."""

  @pytest.fixture
  def changelog(self: TestChangelogDraft, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the changelog into a temporary directory, seeded."""
    path = tmp_path / "CHANGELOG.md"
    path.write_text(CHANGELOG_SEED, encoding="utf-8")
    monkeypatch.setattr(pipeline, "CHANGELOG", path)
    return path

  def test_draft_added_on_change(self: TestChangelogDraft, report: Path, changelog: Path) -> None:
    """A changed source puts a marked draft directly under Unreleased."""
    report.write_text(change_report(changed=True), encoding="utf-8")

    pipeline.draft_changelog()

    text = changelog.read_text(encoding="utf-8")
    block = text.split("## [Unreleased]\n\n", 1)[1].split("\n\n### Added", 1)[0]
    assert block.startswith("<!-- draft ")
    assert block.endswith(" -->")
    assert "<!-- end draft " in block
    assert "- Upstream `cli`: 2026.10.1 → 2026.11.0" in block
    assert "`Source`" not in block
    assert "- Upstream spec: Route added: `GET /new`" in block
    assert "- bw serve routes: Added: `GET /new`" in block
    assert "Drafted an entry" in report.read_text(encoding="utf-8")

  def test_human_entries_untouched(self: TestChangelogDraft, report: Path, changelog: Path) -> None:
    """Removing the inserted block gives back the file exactly as it was."""
    report.write_text(change_report(changed=True), encoding="utf-8")

    pipeline.draft_changelog()

    text = changelog.read_text(encoding="utf-8")
    start, end = text.index("<!-- draft "), text.index("<!-- end draft ")
    end = text.index("-->", end) + len("-->\n\n")
    assert text[:start] + text[end:] == CHANGELOG_SEED

  def test_idempotent_on_rerun(self: TestChangelogDraft, report: Path, changelog: Path) -> None:
    """A second run on the same report adds nothing."""
    report.write_text(change_report(changed=True), encoding="utf-8")
    pipeline.draft_changelog()
    once = changelog.read_text(encoding="utf-8")

    pipeline.draft_changelog()

    assert changelog.read_text(encoding="utf-8") == once
    assert "Already drafted" in report.read_text(encoding="utf-8")

  def test_no_draft_without_change(self: TestChangelogDraft, report: Path, changelog: Path) -> None:
    """A report with no changed source, a stale fix aside, drafts nothing."""
    text = change_report(changed=False)
    report.write_text(text, encoding="utf-8")

    pipeline.draft_changelog()

    assert changelog.read_text(encoding="utf-8") == CHANGELOG_SEED
    assert report.read_text(encoding="utf-8") == text

  @pytest.mark.usefixtures("report")
  def test_no_draft_without_report(self: TestChangelogDraft, changelog: Path) -> None:
    """No report, nothing to draft from."""
    pipeline.draft_changelog()

    assert changelog.read_text(encoding="utf-8") == CHANGELOG_SEED

  def test_missing_changelog(self: TestChangelogDraft, report: Path, changelog: Path) -> None:
    """A missing changelog is not created; the report says why."""
    changelog.unlink()
    report.write_text(change_report(changed=True), encoding="utf-8")

    pipeline.draft_changelog()

    assert not changelog.exists()
    assert "No draft: `CHANGELOG.md` is missing." in report.read_text(encoding="utf-8")

  def test_changelog_without_unreleased(self: TestChangelogDraft, report: Path, changelog: Path) -> None:
    """A changelog with no Unreleased heading is left alone; the report says why."""
    changelog.write_text("# Changelog\n\n## [0.1.0]\n", encoding="utf-8")
    report.write_text(change_report(changed=True), encoding="utf-8")

    pipeline.draft_changelog()

    assert changelog.read_text(encoding="utf-8") == "# Changelog\n\n## [0.1.0]\n"
    assert "has no `## [Unreleased]` heading" in report.read_text(encoding="utf-8")

  @pytest.mark.parametrize(("code", "drafted"), [(0, False), (2, True), (1, False), (-9, False)])
  def test_detect_drafts_only_on_change(self: TestChangelogDraft, mocker: MockerFixture, code: int, drafted: bool) -> None:
    """Detect drafts only after a run that reported a change, keeping its exit code."""
    mocker.patch.object(pipeline.subprocess, "run", return_value=finished(code))
    draft = mocker.patch.object(pipeline, "draft_changelog")

    assert pipeline.detect() == code
    assert draft.called is drafted


class TestUpdate:
  """Update: the stages combined."""

  @pytest.mark.parametrize(
    ("codes", "expected", "ran"),
    [
      ((0, 0, 0), 0, 3),
      ((2, 0, 0), 2, 3),
      ((0, 2, 0), 2, 3),
      ((2, 0, 2), 2, 3),
      ((1, 0, 0), 1, 1),
      ((2, 1, 0), 1, 2),
    ],
  )
  def test_combined_exit_code(
    self: TestUpdate, monkeypatch: pytest.MonkeyPatch, codes: tuple[int, int, int], expected: int, ran: int
  ) -> None:
    """An error stops the run; otherwise any change makes the run a change."""
    calls: List[str] = []
    for name, code in zip(("detect", "build", "check"), codes, strict=True):
      monkeypatch.setattr(pipeline, name, lambda name=name, code=code: calls.append(name) or code)

    assert pipeline.update() == expected
    assert len(calls) == ran


class TestMain:
  """Argument handling."""

  @pytest.mark.parametrize("argv", [[], ["deploy"], ["detect", "build"]])
  def test_bad_arguments_are_an_error(self: TestMain, argv: List[str], capsys: pytest.CaptureFixture[str]) -> None:
    """Anything but one known stage prints usage and exits 1."""
    assert pipeline.main(argv) == 1
    assert "usage: pipeline.py" in capsys.readouterr().err

  def test_dispatches_to_stage(self: TestMain, monkeypatch: pytest.MonkeyPatch) -> None:
    """A stage name runs that stage and returns its code."""
    monkeypatch.setitem(pipeline.STAGES, "check", lambda: 2)

    assert pipeline.main(["check"]) == 2
