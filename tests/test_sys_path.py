"""Collecting the suite leaves ``sys.path`` and the tool names alone (#103).

A test module that puts ``upstream/`` or ``codegen/`` on ``sys.path`` makes
``detect`` or ``generate`` importable for the whole session, and a module
cached under that generic name can then couple tests that have nothing to
do with each other. ``_loader.load_tool`` is how a test loads a tool
instead.

The check collects the whole suite in a child interpreter, so it sees every
module's import-time effects from a clean start, whatever order this
session happened to import them in. It goes red when any test module adds
to ``sys.path`` while being collected, or leaves a tool importable under
its bare name.

It does not see a change made inside a test body or a fixture: collection
runs no tests. Those are already undone by ``monkeypatch.syspath_prepend``,
which is the idiom for that case.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, Set

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"

# Run in the child: snapshot, collect the suite in-process, compare. pytest's
# default import mode puts the test directory first on sys.path unless it is
# already first, so the probe puts it there before the snapshot: any
# difference after that is a test module's. Coverage and the cache are
# switched off because they are irrelevant here and would write files.
PROBE = """
import json, sys
import pytest

sys.path.insert(0, sys.argv[1])
before = list(sys.path)
code = pytest.main(["--collect-only", "-q", "--no-cov", "-p", "no:cacheprovider", sys.argv[1]])
print(json.dumps({"code": int(code), "before": before, "after": list(sys.path), "modules": sorted(sys.modules)}))
"""


def tool_names() -> Set[str]:
  """Every name a repository tool would import under bare.

  Derived from the tree, so a new tool is covered without editing this
  list: each ``.py`` file in ``upstream/``, ``codegen/`` and the repository
  root, its stem with ``-`` read as ``_``.

  Returns:
      Set[str]: The names.
  """
  files = [*ROOT.glob("*.py"), *(ROOT / "upstream").glob("*.py"), *(ROOT / "codegen").glob("*.py")]
  return {path.stem.replace("-", "_") for path in files}


def collect() -> Dict[str, Any]:
  """Collect the suite in a child interpreter and report what it changed.

  Returns:
      Dict[str, Any]: pytest's exit code, ``sys.path`` before and after,
      and every module name loaded once collection finished.
  """
  result = subprocess.run(  # noqa: S603 - runs this interpreter with a fixed script. # nosec B603
    [sys.executable, "-c", PROBE, str(TESTS)],
    capture_output=True,
    text=True,
    cwd=ROOT,
    check=False,
  )
  assert result.returncode == 0, result.stdout + result.stderr

  return json.loads(result.stdout.splitlines()[-1])


class TestCollection:
  """What collecting the whole suite leaves behind."""

  def test_tool_names_are_derived(self: TestCollection) -> None:
    """The name set reaches every tool directory, so the check below is not vacuous."""
    assert {"detect", "spec_fixes", "generate", "pipeline"} <= tool_names()

  def test_leaves_sys_path_and_tool_names_alone(self: TestCollection) -> None:
    """``sys.path`` is unchanged and no tool is importable by its bare name."""
    report = collect()

    assert report["code"] == 0
    assert report["after"] == report["before"]
    assert sorted(tool_names() & set(report["modules"])) == []
