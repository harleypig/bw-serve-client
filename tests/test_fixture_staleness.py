"""Recorded fixtures checked against the pinned CLI release (#105).

``upstream/detect.py`` lists, in its change report, every recorded payload
in ``tests/fixtures/serve/`` whose ``recorded.cli`` differs from the
release pinned in ``upstream/lock.json``. A pin that moves makes every
payload stale at once, so the listing must never change detect's exit
code: the update pipeline keeps running until someone re-records.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Dict, TYPE_CHECKING

import pytest

if TYPE_CHECKING:
  from types import ModuleType

UPSTREAM = Path(__file__).resolve().parent.parent / "upstream"
PIN = "cli-v2026.11.0"


def _load(name: str, filename: str) -> ModuleType:
  """Load an ``upstream/`` module by path, under a name no other module uses.

  The module is registered under that name, as dataclasses need to find
  their module in ``sys.modules``.

  Arguments:
    name: The module name to load it under.
    filename: The file in ``upstream/``.

  Returns:
    The loaded module.
  """
  spec = importlib.util.spec_from_file_location(name, UPSTREAM / filename)
  assert spec is not None
  assert spec.loader is not None
  module = importlib.util.module_from_spec(spec)
  sys.modules[name] = module
  spec.loader.exec_module(module)

  return module


def _load_detect() -> ModuleType:
  """Load ``upstream/detect.py`` by path, leaving ``sys.path`` alone.

  detect does a bare ``import spec_fixes``, so that one name is lent to
  ``sys.modules`` while detect loads, and taken back after unless something
  else had already imported it.

  Returns:
    The loaded module.
  """
  lent = "spec_fixes" not in sys.modules
  if lent:
    sys.modules["spec_fixes"] = _load("_bw_upstream_spec_fixes_for_fixture_staleness", "spec_fixes.py")

  try:
    return _load("_bw_upstream_detect_for_fixture_staleness", "detect.py")

  finally:
    if lent:
      del sys.modules["spec_fixes"]


detect = _load_detect()


def write_fixture(directory: Path, name: str, content: Any) -> None:
  """Write one recorded payload.

  Arguments:
    directory: The fixtures directory.
    name: The file name.
    content: The JSON content, or a ``str`` written as is.
  """
  text = content if isinstance(content, str) else json.dumps(content)
  (directory / name).write_text(text, encoding="utf-8")


def recorded(cli: str) -> Dict[str, Any]:
  """Build a payload recorded with the given CLI version.

  Arguments:
    cli: The CLI version, without the tag prefix.

  Returns:
    The payload.
  """
  return {"case": "x", "recorded": {"cli": cli, "date": "2026-11-01"}, "request": {}, "response": {}}


class TestStaleFixtures:
  """Comparing each payload's recorded CLI version with the pin."""

  def test_match_lists_nothing(self: TestStaleFixtures, tmp_path: Path) -> None:
    """Payloads recorded with the pinned release are not listed."""
    write_fixture(tmp_path, "a.json", recorded("2026.11.0"))
    write_fixture(tmp_path, "b.json", recorded("2026.11.0"))

    assert detect.stale_fixtures(tmp_path, PIN) == []

  def test_mismatch_grouped_by_version(self: TestStaleFixtures, tmp_path: Path) -> None:
    """Each differing version gives one line naming its payloads."""
    write_fixture(tmp_path, "b.json", recorded("2026.10.1"))
    write_fixture(tmp_path, "a.json", recorded("2026.10.1"))
    write_fixture(tmp_path, "c.json", recorded("2026.9.0"))
    write_fixture(tmp_path, "d.json", recorded("2026.11.0"))

    assert detect.stale_fixtures(tmp_path, PIN) == [
      "2 recorded with bw CLI 2026.10.1, not the pinned 2026.11.0: `a.json`, `b.json`",
      "1 recorded with bw CLI 2026.9.0, not the pinned 2026.11.0: `c.json`",
    ]

  @pytest.mark.parametrize(
    "content", [
      {
        "case": "x"
      },
      {
        "recorded": {
          "date": "2026-11-01"
        }
      },
      {
        "recorded": {
          "cli": ""
        }
      },
      {
        "recorded": "2026.11.0"
      },
    ],
    ids=["no-recorded", "no-cli", "empty-cli", "recorded-not-an-object"]
  )
  def test_missing_version_listed(self: TestStaleFixtures, tmp_path: Path, content: Dict[str, Any]) -> None:
    """A payload naming no CLI version is listed, never taken as a match."""
    write_fixture(tmp_path, "a.json", content)

    assert detect.stale_fixtures(tmp_path, PIN) == ["1 record no bw CLI version: `a.json`"]

  @pytest.mark.parametrize("content", ["{not json", "[]"], ids=["malformed", "not-an-object"])
  def test_unreadable_listed(self: TestStaleFixtures, tmp_path: Path, content: str) -> None:
    """A payload that is not a JSON object is listed rather than raising."""
    write_fixture(tmp_path, "a.json", content)

    assert detect.stale_fixtures(tmp_path, PIN) == ["1 could not be read as JSON: `a.json`"]

  def test_only_json_files_read(self: TestStaleFixtures, tmp_path: Path) -> None:
    """Other files in the directory are not payloads."""
    write_fixture(tmp_path, "README.md", "# not a payload")

    assert detect.stale_fixtures(tmp_path, PIN) == []

  def test_committed_payloads_are_found(self: TestStaleFixtures) -> None:
    """The real fixtures directory holds payloads the check reads.

    Guards against the check going vacuous: a moved directory would list
    nothing and read as every payload matching.
    """
    payloads = len(list(detect.SERVE_FIXTURES_DIR.glob("*.json")))

    stale = detect.stale_fixtures(detect.SERVE_FIXTURES_DIR, "cli-v0.0.0")

    assert payloads > 0
    assert sum(int(line.split(" ", 1)[0]) for line in stale) == payloads


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
  """Point every file detect reads or writes into a temporary directory.

  Upstream is fixed at one minimal state pinned to ``PIN``, so every run
  after the first finds nothing changed.
  """
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

  upstream = detect.Upstream({"paths": {}}, PIN, {}, [], {}, {})
  monkeypatch.setattr(detect, "fetch_all", lambda session, watch: upstream)  # noqa: U100 - matches fetch_all's signature.
  return tmp_path


def run(repo: Path) -> int:
  """Run detection once against the fixed upstream.

  Arguments:
    repo: The temporary directory.

  Returns:
    detect's exit code.
  """
  return detect.run(None, repo / "change-report.md", "2026-11-03")


class TestRun:
  """The listing in a full detect run, and its exit code."""

  def test_match_reported_as_none(self: TestRun, repo: Path) -> None:
    """With every payload current the section says so, and the run exits 0."""
    write_fixture(repo / "serve", "a.json", recorded("2026.11.0"))
    run(repo)

    code = run(repo)

    report = (repo / "change-report.md").read_text(encoding="utf-8")
    assert code == 0
    assert "## Recorded fixtures\n\nNone; every fixture was recorded with the pinned CLI.\n" in report

  def test_mismatch_reported_without_changing_exit_code(self: TestRun, repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A stale payload is in the report and on stdout, and the run still exits 0."""
    write_fixture(repo / "serve", "a.json", recorded("2026.10.1"))
    write_fixture(repo / "serve", "b.json", {"case": "b"})
    run(repo)
    capsys.readouterr()

    code = run(repo)

    report = (repo / "change-report.md").read_text(encoding="utf-8")
    assert code == 0
    assert "- 1 recorded with bw CLI 2026.10.1, not the pinned 2026.11.0: `a.json`\n" in report
    assert "- 1 record no bw CLI version: `b.json`\n" in report
    assert "Some recorded fixtures name another CLI version" in report
    assert "detect: warning: recorded fixtures differ from the pinned CLI" in capsys.readouterr().out

  def test_mismatch_leaves_a_change_at_exit_2(self: TestRun, repo: Path) -> None:
    """A run that finds a change still exits 2, stale payloads or not."""
    write_fixture(repo / "serve", "a.json", recorded("2026.10.1"))

    code = run(repo)

    assert code == 2
    assert "`a.json`" in (repo / "change-report.md").read_text(encoding="utf-8")
