"""Tests for the fixture recorder's placeholder filling and payload writing.

The recorder itself needs Docker, so only the parts that do not are tested:
how a case's placeholders are filled from earlier responses, how a run's
payloads replace the ones on disk, and what the cleanup asks Docker to do.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
  from types import ModuleType

RECORDER = Path(__file__).resolve().parent / "fixtures" / "recorder" / "record.py"


def _load_recorder() -> ModuleType:
  """Load the recorder script by path, under a name no other module uses.

  Returns:
    The loaded module.
  """
  spec = importlib.util.spec_from_file_location("_bw_fixture_recorder", RECORDER)
  assert spec is not None
  assert spec.loader is not None
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)

  return module


record = _load_recorder()

FOLDER_ID = "3a84be8d-12e7-4223-98cd-ae0000eabdec"


def _case(name: str) -> object:
  """Return the recorder's case of that name.

  Args:
    name: The case name.

  Returns:
    The case.
  """
  return next(case for case in record.CASES if case.name == name)


# -----------------------------------------------------------------------------
class TestFill:
  """Placeholders are filled from kept values, or the case fails loudly."""

  def test_fills_path_placeholder(self: TestFill) -> None:
    """A path placeholder takes the value an earlier case kept."""
    path, data = record.fill(_case("folder-get"), {"folder_id": FOLDER_ID})  # act

    assert path == f"/object/folder/{FOLDER_ID}"
    assert data is None

  def test_fills_body_placeholder(self: TestFill) -> None:
    """A placeholder inside the JSON body is filled too."""
    _path, data = record.fill(_case("item-create"), {"folder_id": FOLDER_ID})  # act

    assert json.loads(data)["folderId"] == FOLDER_ID

  def test_sends_raw_body_as_written(self: TestFill) -> None:
    """A raw body is not treated as a template, so its braces survive."""
    _path, data = record.fill(_case("folder-create-malformed-json"), {})  # act

    assert data == "{not json"

  @pytest.mark.parametrize("name", ["folder-get", "item-create"])
  def test_missing_value_names_case_and_key(self: TestFill, name: str) -> None:
    """A missing value is a RuntimeError naming the case and the key.

    It must be the error ``record()`` catches, so the container log is
    attached, and nothing may be sent with the placeholder left empty.
    """
    with pytest.raises(RuntimeError, match=rf"^{name}: no value for {{folder_id}}"):
      record.fill(_case(name), {})


# -----------------------------------------------------------------------------
class TestWritePayloads:
  """A run's payloads replace the directory's, leaving no stale file."""

  def test_removes_stale_payloads(self: TestWritePayloads, tmp_path: Path) -> None:
    """A payload no case wrote this run is removed; other files are left."""
    (tmp_path / "renamed-case.json").write_text("{}\n")
    (tmp_path / "README.md").write_text("kept\n")
    payload = {"case": "status-locked", "response": {"status": 200}}

    record.write_payloads(tmp_path, [payload])  # act

    assert sorted(p.name for p in tmp_path.iterdir()) == ["README.md", "status-locked.json"]
    assert json.loads((tmp_path / "status-locked.json").read_text()) == payload


# -----------------------------------------------------------------------------
def _not_ready(base: str, container: str) -> None:  # noqa: U100 - stands in for wait_ready; no use for them.
  """Fail the way a bw serve that never answers does.

  Raises:
    RuntimeError: Always.
  """
  raise RuntimeError("bw serve never answered")


# -----------------------------------------------------------------------------
class _FakeDocker:
  """Records each docker() call and answers with a made-up container id."""

  def __init__(self: _FakeDocker) -> None:
    self.calls: list[tuple[str, ...]] = []

  def __call__(self: _FakeDocker, *args: str, **kwargs: object) -> str:  # noqa: U100 - takes docker()'s keywords; no use for them.
    """Record the call.

    Args:
      args: The docker arguments.
      kwargs: docker()'s keyword options, ignored.

    Returns:
      A made-up container id.
    """
    self.calls.append(args)

    return f"container-{len(self.calls)}"


# -----------------------------------------------------------------------------
class TestCleanup:
  """A run removes its containers together with their anonymous volumes."""

  def test_failed_run_removes_container_volumes(self: TestCleanup, monkeypatch: pytest.MonkeyPatch) -> None:
    """Every container removal passes --volumes, even when the run fails.

    The Vaultwarden image declares ``VOLUME /data``, so a removal without
    ``--volumes`` leaves one anonymous volume behind per run (#109).
    """
    fake = _FakeDocker()
    monkeypatch.setattr(record, "docker", fake)
    monkeypatch.setattr(record, "wait_ready", _not_ready)

    with pytest.raises(RuntimeError, match="never answered"):
      record.record(8087, keep_image=True)  # act

    removals = [c for c in fake.calls if c[0] == "rm"]
    assert len(removals) == 2
    assert all("--volumes" in c for c in removals)
