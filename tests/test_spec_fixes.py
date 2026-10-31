"""Tests for the name-keyed spec fixes (upstream/spec_fixes.py)."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Dict, List

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "upstream"))

import spec_fixes  # noqa: E402 - importable only once upstream/ is on the path.

UPSTREAM = Path(__file__).resolve().parent.parent / "upstream"

PARAMS = ["paths", "/items", "get", "parameters"]


def spec() -> Dict[str, Any]:
  """Build a small spec with two parameters and one schema.

  Returns:
      Dict[str, Any]: The spec.
  """
  return {
    "paths": {
      "/items": {
        "get": {
          "parameters": [
            {
              "in": "query",
              "name": "search",
              "schema": {
                "type": "string"
              }
            },
            {
              "in": "query",
              "name": "url",
              "schema": {
                "type": "string",
                "format": "url"
              }
            },
          ]
        }
      }
    },
    "components": {
      "schemas": {
        "item": {
          "type": "object"
        }
      }
    },
  }


def apply(*fixes: Dict[str, Any]) -> tuple[Dict[str, Any], List[str]]:
  """Apply fixes to a fresh copy of the small spec.

  Arguments:
      fixes: The fix entries.

  Returns:
      tuple[Dict[str, Any], List[str]]: The patched spec and the problems.
  """
  return spec_fixes.apply_fixes(spec(), list(fixes))


class TestOperations:
  """Each operation, where it matches and where it refuses."""

  def test_add_by_selector(self: TestOperations) -> None:
    """A selector finds the parameter by name, wherever it sits."""
    patched, problems = apply({"op": "add", "path": [*PARAMS, {"name": "search"}, "schema", "title"], "value": "SearchSchema"})

    assert problems == []
    assert patched["paths"]["/items"]["get"]["parameters"][0]["schema"]["title"] == "SearchSchema"

  def test_add_refuses_existing_key(self: TestOperations) -> None:
    """An add whose key already exists is stale: upstream may supply it now."""
    _, problems = apply({"op": "add", "path": [*PARAMS, {"name": "search"}, "schema", "type"], "value": "string"})

    assert problems == [
      "fix 1 (add paths › /items › get › parameters[name=search] › schema › type): 'type' already exists (upstream may now supply it)"
    ]

  def test_set_checks_the_current_value(self: TestOperations) -> None:
    """A set replaces the value it expects, and refuses any other."""
    path = [*PARAMS, {"in": "query", "name": "url"}, "schema", "format"]

    patched, problems = apply({"op": "set", "path": path, "from": "url", "value": "uri"})
    _, stale = apply({"op": "set", "path": path, "from": "hostname", "value": "uri"})

    assert problems == []
    assert patched["paths"]["/items"]["get"]["parameters"][1]["schema"]["format"] == "uri"
    assert stale == [
      "fix 1 (set paths › /items › get › parameters[in=query,name=url] › schema › format): "
      "current value 'url' is not the expected 'hostname'"
    ]

  def test_delete_checks_the_current_value(self: TestOperations) -> None:
    """A delete removes the key only when it holds the expected value."""
    path = [*PARAMS, {"name": "url"}, "schema", "format"]

    patched, problems = apply({"op": "delete", "path": path, "from": "url"})
    _, stale = apply({"op": "delete", "path": path, "from": "uri"})

    assert problems == []
    assert "format" not in patched["paths"]["/items"]["get"]["parameters"][1]["schema"]
    assert len(stale) == 1

  def test_append_a_named_element(self: TestOperations) -> None:
    """An append adds an element, and refuses one whose name is taken."""
    element = {"in": "query", "name": "permanent", "schema": {"type": "boolean"}}

    patched, problems = apply({"op": "append", "path": PARAMS, "value": element})
    _, taken = apply({"op": "append", "path": PARAMS, "value": {"in": "query", "name": "search"}})

    assert problems == []
    assert patched["paths"]["/items"]["get"]["parameters"][-1] == element
    assert taken == [
      "fix 1 (append paths › /items › get › parameters): an element matching "
      "{'in': 'query', 'name': 'search'} already exists (upstream may now supply it)"
    ]

  def test_append_without_in_matches_only_elements_without_in(self: TestOperations) -> None:
    """A named element with no ``in`` is not the same as a query parameter of that name."""
    patched, problems = apply({"op": "append", "path": PARAMS, "value": {"name": "search"}})
    _, taken = apply({
      "op": "append",
      "path": PARAMS,
      "value": {
        "name": "search"
      }
    }, {
      "op": "append",
      "path": PARAMS,
      "value": {
        "name": "search"
      }
    })

    assert problems == []
    assert patched["paths"]["/items"]["get"]["parameters"][-1] == {"name": "search"}
    assert len(taken) == 1
    assert taken[0].startswith("fix 2 ")

  def test_append_an_unnamed_element(self: TestOperations) -> None:
    """An unnamed element is refused only when an equal one is present."""
    path = ["components", "schemas", "item", "required"]
    raw = spec()
    raw["components"]["schemas"]["item"]["required"] = ["id"]

    patched, problems = spec_fixes.apply_fixes(raw, [{"op": "append", "path": path, "value": "name"}])
    _, duplicate = spec_fixes.apply_fixes(raw, [{"op": "append", "path": path, "value": "id"}])

    assert problems == []
    assert patched["components"]["schemas"]["item"]["required"] == ["id", "name"]
    assert duplicate == [
      "fix 1 (append components › schemas › item › required): the element is already in the array (upstream may now supply it)"
    ]

  def test_append_needs_an_array(self: TestOperations) -> None:
    """An append onto anything but an array is refused."""
    _, problems = apply({"op": "append", "path": ["components", "schemas", "item"], "value": 1})

    assert problems == ["fix 1 (append components › schemas › item): 'item' is not an array"]

  def test_raw_spec_is_not_changed(self: TestOperations) -> None:
    """Applying works on a copy."""
    raw = spec()

    spec_fixes.apply_fixes(raw, [{"op": "add", "path": ["components", "schemas", "item", "title"], "value": "ItemSchema"}])

    assert raw == spec()


class TestMatching:
  """Every fix must match exactly one target."""

  # yapf: disable
  @pytest.mark.parametrize(
    ("path", "message"),
    [
      ([*PARAMS, {"name": "gone"}, "schema", "title"], "matches 0 elements, not 1"),
      ([*PARAMS, {"in": "query"}, "schema", "title"], "matches 2 elements, not 1"),
      (["paths", "/gone", "get", "summary"], "key '/gone' not found"),
      (["paths", {"name": "x"}, "title"], "applied to a dict, not an array"),
      ([*PARAMS, "title"], "parent of 'title' is a list, not an object"),
    ],
  )
  # yapf: enable
  def test_ambiguous_or_missing_target(self: TestMatching, path: List[Any], message: str) -> None:
    """A target that is gone or ambiguous names the fix and the reason."""
    _, problems = apply({"op": "add", "path": path, "value": "x"})

    assert len(problems) == 1
    assert message in problems[0]

  def test_null_selector_needs_the_key(self: TestMatching) -> None:
    """A selector value of null matches only an element holding null, not one missing the key."""
    _, problems = apply({"op": "add", "path": [*PARAMS, {"in": "query", "required": None}, "schema", "title"], "value": "x"})

    assert len(problems) == 1
    assert "matches 0 elements, not 1" in problems[0]

  def test_every_failure_is_reported(self: TestMatching) -> None:
    """All failing fixes are listed, each with its number, not just the first."""
    _, problems = apply(
      {
        "op": "add",
        "path": ["paths", "/gone", "title"],
        "value": "x"
      },
      {
        "op": "add",
        "path": ["components", "schemas", "item", "title"],
        "value": "ItemSchema"
      },
      {
        "op": "set",
        "path": ["components", "schemas", "item", "type"],
        "from": "string",
        "value": "object"
      },
    )

    assert [problem.split(" ")[1] for problem in problems] == ["1", "3"]

  @pytest.mark.parametrize(
    ("entry", "message"),
    [
      ({
        "op": "rename",
        "path": ["a"]
      }, "unknown op 'rename'"),
      ({
        "op": "add",
        "path": []
      }, "non-empty list ending in an object key"),
      ({
        "op": "add",
        "path": ["a", {}],
        "value": 1
      }, "non-empty list ending in an object key"),
      ({
        "op": "add",
        "path": ["a", {}, "b"],
        "value": 1
      }, "non-empty selector"),
      ({
        "op": "add",
        "path": ["a"]
      }, "add needs a value"),
      ({
        "op": "set",
        "path": ["a"],
        "value": 1
      }, "set needs a from"),
      (["op", "add"], "entry is a list, not an object"),
      ("add", "entry is a str, not an object"),
    ],
  )
  def test_malformed_fix(self: TestMatching, entry: Any, message: str) -> None:
    """A malformed entry is a failing fix, not a crash."""
    _, problems = apply(entry)

    assert len(problems) == 1
    assert message in problems[0]


class TestCommandLine:
  """The apply and check commands."""

  @pytest.fixture
  def files(self: TestCommandLine, tmp_path: Path) -> Dict[str, Path]:
    """Write a raw spec and a fixes file into a temporary directory.

    Arguments:
        tmp_path: pytest's temporary directory.

    Returns:
        Dict[str, Path]: The raw, fixes and out paths.
    """
    paths = {"raw": tmp_path / "raw.json", "fixes": tmp_path / "fixes.json", "out": tmp_path / "patched.json"}
    paths["raw"].write_text(json.dumps(spec()), encoding="utf-8")
    return paths

  def run(self: TestCommandLine, files: Dict[str, Path], command: str, fixes: List[Dict[str, Any]]) -> int:
    """Write the fixes and run the command against the temporary files.

    Arguments:
        files: The paths from the files fixture.
        command: ``apply`` or ``check``.
        fixes: The fix entries.

    Returns:
        int: The exit code.
    """
    files["fixes"].write_text(json.dumps({"fixes": fixes}), encoding="utf-8")
    args = ["--raw", str(files["raw"]), "--fixes", str(files["fixes"]), "--out", str(files["out"])]
    return spec_fixes.main([command, *args])

  def test_apply_writes_the_patched_spec(self: TestCommandLine, files: Dict[str, Path]) -> None:
    """A clean apply exits 0 and writes the result."""
    code = self.run(files, "apply", [{"op": "add", "path": ["components", "schemas", "item", "title"], "value": "ItemSchema"}])

    assert code == 0
    assert json.loads(files["out"].read_text(encoding="utf-8"))["components"]["schemas"]["item"]["title"] == "ItemSchema"

  def test_failing_fix_writes_nothing(self: TestCommandLine, files: Dict[str, Path], capsys: pytest.CaptureFixture[str]) -> None:
    """One failing fix exits 1, names it, and writes no patched spec."""
    code = self.run(files, "apply", [{"op": "add", "path": ["paths", "/gone", "title"], "value": "x"}])

    assert code == 1
    assert not files["out"].exists()
    assert "fix 1 (add paths › /gone › title): key '/gone' not found" in capsys.readouterr().err

  def test_check_never_writes(self: TestCommandLine, files: Dict[str, Path]) -> None:
    """Check reports success without writing."""
    code = self.run(files, "check", [])

    assert code == 0
    assert not files["out"].exists()

  def test_fixes_file_without_a_fixes_list(self: TestCommandLine, files: Dict[str, Path]) -> None:
    """A fixes file in the old format is an error, not an empty fix set."""
    files["fixes"].write_text(json.dumps({"operations": []}), encoding="utf-8")

    code = spec_fixes.main(["check", "--raw", str(files["raw"]), "--fixes", str(files["fixes"])])

    assert code == 1


class TestCommittedFiles:
  """The committed fixes, raw spec and patched spec agree."""

  def test_fixes_rebuild_the_committed_patched_spec(self: TestCommittedFiles) -> None:
    """Applying the committed fixes to the committed raw spec yields the committed patched spec."""
    raw = json.loads((UPSTREAM / "vault-management-api-original.json").read_text(encoding="utf-8"))
    committed = json.loads((UPSTREAM / "vault-management-api-fixed.json").read_text(encoding="utf-8"))

    patched, problems = spec_fixes.apply_fixes(raw, spec_fixes.load_fixes(UPSTREAM / "spec-fixes.json"))

    assert problems == []
    assert patched == committed

  def test_no_fix_addresses_an_array_by_position(self: TestCommittedFiles) -> None:
    """Every array step in a committed fix is a selector, never an index."""
    for entry in spec_fixes.load_fixes(UPSTREAM / "spec-fixes.json"):
      assert not any(isinstance(segment, str) and segment.isdigit() for segment in entry["path"]), entry["path"]
