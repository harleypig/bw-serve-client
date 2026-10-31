#!/usr/bin/env python3

"""Apply the local spec fixes to the raw spec, by name, never by position.

Each fix in ``upstream/spec-fixes.json`` names its target with a path: a
list whose strings are object keys and whose objects select one array
element by its fields, such as ``{"in": "query", "name": "search"}`` for a
parameter. A selector must match exactly one element, so a fix survives
upstream reordering and fails loudly when its target is ambiguous or gone.

Operations:

- ``add``: set a key that must not exist yet.
- ``set``: replace a value that must currently equal ``from``.
- ``delete``: remove a key whose value must currently equal ``from``.
- ``append``: add an element to the array at a key. An element with a
  ``name`` must not share its ``in`` and ``name`` with one already there;
  any other element must not already be present.

Every fix must match exactly one target, or nothing is written and the run
exits 1, naming each fix that failed. Usage:

- ``python upstream/spec_fixes.py apply`` writes the patched spec.
- ``python upstream/spec_fixes.py check`` only reports.
"""

import argparse
import copy
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any, cast, Dict, List, Optional, Tuple, Union

UPSTREAM_DIR = Path(__file__).resolve().parent
RAW_SPEC = UPSTREAM_DIR / "vault-management-api-original.json"
FIXES_FILE = UPSTREAM_DIR / "spec-fixes.json"
PATCHED_SPEC = UPSTREAM_DIR / "vault-management-api-fixed.json"

OPERATIONS = ("add", "set", "delete", "append")

Segment = Union[str, Dict[str, Any]]


class FixError(Exception):
  """A fix that does not match exactly one target."""


@dataclass
class Fix:
  """One fix, as read from the fixes file.

  Attributes:
      op: ``add``, ``set``, ``delete`` or ``append``.
      path: Object keys and array-element selectors, from the spec's root.
      value: The value to write (``add``, ``set``) or the element to add (``append``).
      expected: The value that must be there now, for ``set`` and ``delete``.
      why: Why the fix exists, where it changes meaning rather than naming.
  """

  op: str
  path: List[Segment]
  value: Any = None
  expected: Any = None
  why: str = ""


# -----------------------------------------------------------------------------
def describe(path: List[Segment]) -> str:
  """Render a fix path for messages.

  Arguments:
      path: Object keys and array-element selectors.

  Returns:
      str: Keys joined by ``›``, selectors as ``[key=value,…]``.
  """
  text = ""

  for segment in path:
    if isinstance(segment, dict):
      text += "[" + ",".join(f"{key}={value}" for key, value in segment.items()) + "]"

    else:
      text += f" › {segment}" if text else segment

  return text


# -----------------------------------------------------------------------------
def _matches(item: Any, selector: Dict[str, Any]) -> bool:
  """Tell whether an array element has every field a selector names.

  A field must be present, not merely absent and compared as None.

  Arguments:
      item: An array element.
      selector: Field names and the values they must hold.

  Returns:
      bool: Whether the element matches.
  """
  return isinstance(item, dict) and all(k in item and item[k] == v for k, v in selector.items())


# -----------------------------------------------------------------------------
def parse_fix(entry: Any) -> Fix:
  """Validate one entry of the fixes file.

  Arguments:
      entry: The entry as decoded from JSON.

  Raises:
      FixError: When the entry is malformed.

  Returns:
      Fix: The fix.
  """
  if not isinstance(entry, dict):
    raise FixError(f"entry is a {type(entry).__name__}, not an object")

  op = entry.get("op")
  path = entry.get("path")

  if op not in OPERATIONS:
    raise FixError(f"unknown op {op!r}; expected one of {', '.join(OPERATIONS)}")

  if not isinstance(path, list) or not path or not isinstance(path[-1], str):
    raise FixError("path must be a non-empty list ending in an object key")

  if not all(isinstance(segment, str) or (isinstance(segment, dict) and segment) for segment in path):
    raise FixError("each path segment must be a key or a non-empty selector object")

  if op in ("add", "set", "append") and "value" not in entry:
    raise FixError(f"{op} needs a value")

  if op in ("set", "delete") and "from" not in entry:
    raise FixError(f"{op} needs a from: the value it expects to replace")

  return Fix(op, path, entry.get("value"), entry.get("from"), entry.get("why", ""))


# -----------------------------------------------------------------------------
def select(node: Any, segment: Segment) -> Any:
  """Step from one node to the next along a path.

  Arguments:
      node: The current node.
      segment: An object key, or a selector for one element of an array.

  Raises:
      FixError: When the key is missing, or the selector matches no element
          or more than one.

  Returns:
      Any: The selected node.
  """
  if isinstance(segment, dict):
    if not isinstance(node, list):
      raise FixError(f"selector {segment} applied to a {type(node).__name__}, not an array")

    matches = [item for item in node if _matches(item, segment)]
    if len(matches) != 1:
      raise FixError(f"selector {segment} matches {len(matches)} elements, not 1")

    return matches[0]

  if not isinstance(node, dict) or segment not in node:
    raise FixError(f"key {segment!r} not found")

  return node[segment]


# -----------------------------------------------------------------------------
def apply_fix(spec: Dict[str, Any], fix: Fix) -> None:
  """Apply one fix in place.

  Arguments:
      spec: The spec to change.
      fix: The fix to apply.

  Raises:
      FixError: When the fix does not match exactly one target.
  """
  parent: Any = spec
  for segment in fix.path[:-1]:
    parent = select(parent, segment)

  # parse_fix has already required the path to end in an object key.
  key = cast("str", fix.path[-1])
  if not isinstance(parent, dict):
    raise FixError(f"parent of {key!r} is a {type(parent).__name__}, not an object")

  if fix.op == "append":
    _append(parent, key, fix.value)
    return

  if fix.op == "add":
    if key in parent:
      raise FixError(f"{key!r} already exists (upstream may now supply it)")

    parent[key] = copy.deepcopy(fix.value)
    return

  if key not in parent:
    raise FixError(f"key {key!r} not found")

  if parent[key] != fix.expected:
    raise FixError(f"current value {parent[key]!r} is not the expected {fix.expected!r}")

  if fix.op == "set":
    parent[key] = copy.deepcopy(fix.value)

  else:
    del parent[key]


# -----------------------------------------------------------------------------
def _append(parent: Dict[str, Any], key: str, element: Any) -> None:
  """Add an element to the array at a key, unless it is already there.

  Arguments:
      parent: The object holding the array.
      key: The array's key.
      element: The element to add.

  Raises:
      FixError: When the key is not an array, or the element is already in it.
  """
  array = parent.get(key)
  if not isinstance(array, list):
    raise FixError(f"{key!r} is not an array")

  if isinstance(element, dict) and "name" in element:
    # Without an "in", only an element that also lacks one is the same one.
    selector = {k: element[k] for k in ("in", "name") if k in element}
    if any(_matches(item, selector) and ("in" in element or "in" not in item) for item in array):
      raise FixError(f"an element matching {selector} already exists (upstream may now supply it)")

  elif element in array:
    raise FixError("the element is already in the array (upstream may now supply it)")

  array.append(copy.deepcopy(element))


# -----------------------------------------------------------------------------
def apply_fixes(raw: Dict[str, Any], entries: List[Any]) -> Tuple[Dict[str, Any], List[str]]:
  """Apply every fix to a copy of the raw spec.

  Every fix is tried, so one run names every fix that fails.

  Arguments:
      raw: The raw spec; it is not changed.
      entries: The ``fixes`` list from the fixes file.

  Returns:
      Tuple[Dict[str, Any], List[str]]: The patched spec, and one line per
      fix that failed, which is empty when every fix matched.
  """
  patched = copy.deepcopy(raw)
  problems: List[str] = []

  for number, entry in enumerate(entries, start=1):
    try:
      fix = parse_fix(entry)
      apply_fix(patched, fix)

    except FixError as exc:
      fields = entry if isinstance(entry, dict) else {}
      where = describe(fields["path"]) if isinstance(fields.get("path"), list) else "?"
      problems.append(f"fix {number} ({fields.get('op', '?')} {where}): {exc}")

  return patched, problems


# -----------------------------------------------------------------------------
def load_fixes(path: Path) -> List[Dict[str, Any]]:
  """Read the ``fixes`` list from a fixes file.

  Arguments:
      path: The fixes file.

  Raises:
      FixError: When the file has no ``fixes`` list.

  Returns:
      List[Dict[str, Any]]: The entries.
  """
  data = json.loads(path.read_text(encoding="utf-8"))
  fixes = data.get("fixes") if isinstance(data, dict) else None

  if not isinstance(fixes, list):
    raise FixError(f"{path.name} has no fixes list")

  return fixes


# -----------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
  """Apply or check the fixes.

  Arguments:
      argv: The command-line arguments, without the program name.

  Returns:
      int: 0 when every fix matched, 1 otherwise.
  """
  parser = argparse.ArgumentParser(description="Apply the local spec fixes to the raw spec.")
  parser.add_argument("command", choices=("apply", "check"), help="apply writes the patched spec; check only reports")
  parser.add_argument("--raw", type=Path, default=RAW_SPEC, help="the raw spec")
  parser.add_argument("--fixes", type=Path, default=FIXES_FILE, help="the fixes file")
  parser.add_argument("--out", type=Path, default=PATCHED_SPEC, help="where apply writes the patched spec")
  args = parser.parse_args(argv)

  try:
    raw = json.loads(args.raw.read_text(encoding="utf-8"))
    patched, problems = apply_fixes(raw, load_fixes(args.fixes))

  except (OSError, ValueError, FixError) as exc:
    print(f"spec_fixes: error: {exc}", file=sys.stderr)
    return 1

  if problems:
    print(f"spec_fixes: {len(problems)} fix(es) do not match exactly one target; nothing written:", file=sys.stderr)
    print("\n".join(problems), file=sys.stderr)
    return 1

  if args.command == "apply":
    args.out.write_text(json.dumps(patched, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

  return 0


if __name__ == "__main__":
  sys.exit(main())
