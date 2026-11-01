"""Every spec route is implemented by a resource method or excluded with a reason.

A route is implemented when a method of a resource class declares it with
``@route``; it is excluded when ``route_exclusions.json`` lists it with a
reason. The check runs in both directions, so it goes red on:

- a spec route that is neither -- how a new upstream route shows up;
- a declared route the spec does not have (a typo, or a removed route);
- a route declared by two methods;
- an exclusion the spec no longer has, or one a method now implements;
- an exclusion with no reason, or a "not yet implemented" one that names
  no issue.

What it does not check: that a method's ``_request`` call uses the route it
declares. The wire tests in ``test_folders.py`` pin the method and path each
call sends, and the docstring test catches two methods' declarations being
swapped, since each docstring carries its own route's summary.
"""

from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import re
from typing import Any, TYPE_CHECKING

from _routes import resource_methods
import pytest

from bw_serve_client._generated import routes as routes_module
from bw_serve_client._generated.routes import Route
from bw_serve_client.resource import RouteKey

if TYPE_CHECKING:
  from collections.abc import Iterable, Mapping, Sequence

EXCLUSIONS_FILE = Path(__file__).with_name("route_exclusions.json")

NOT_YET = "not yet implemented"

# The spec as imported, before any test monkeypatches ROUTES.
IMPORTED_ROUTES = routes_module.ROUTES

# The routes Folders implements: the known positive that proves discovery
# reaches a real resource class rather than returning nothing.
FOLDER_ROUTES = {
  RouteKey("POST", "/object/folder"): "Folders.add",
  RouteKey("PUT", "/object/folder/{id}"): "Folders.modify",
  RouteKey("GET", "/object/folder/{id}"): "Folders.get",
  RouteKey("DELETE", "/object/folder/{id}"): "Folders.delete",
  RouteKey("GET", "/list/object/folders"): "Folders.list",
}


# -----------------------------------------------------------------------------
def declarations() -> dict[RouteKey, list[str]]:
  """Map each declared route to the methods that declare it.

  Returns:
    Route to ``Class.method`` names; more than one name is a defect.
  """
  owners: dict[RouteKey, list[str]] = defaultdict(list)

  for cls, name, keys in resource_methods():
    for key in keys:
      owners[key].append(f"{cls.__name__}.{name}")

  return dict(owners)


# -----------------------------------------------------------------------------
def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
  """Build a JSON object, refusing a key that appears twice.

  ``json`` keeps the last of two equal keys, which would hide an entry.

  Args:
    pairs: The object's members, in file order.

  Returns:
    The object.

  Raises:
    ValueError: When a key appears more than once.
  """
  result: dict[str, Any] = {}

  for key, value in pairs:
    if key in result:
      raise ValueError(f"duplicate key in {EXCLUSIONS_FILE.name}: {key}")

    result[key] = value

  return result


# -----------------------------------------------------------------------------
def load_exclusions(path: Path = EXCLUSIONS_FILE) -> dict[str, str]:
  """Read the exclusion list.

  Args:
    path: The JSON file.

  Returns:
    ``METHOD /path`` to the reason it is excluded.
  """
  return json.loads(path.read_text(), object_pairs_hook=_no_duplicate_keys)["routes"]


# -----------------------------------------------------------------------------
def coverage_problems(
  routes: Iterable[Route],
  declared: Mapping[RouteKey, Sequence[str]],
  exclusions: Mapping[str, str],
) -> list[str]:
  """Compare the spec's routes with the declarations and the exclusions.

  Args:
    routes: The spec's routes.
    declared: Each declared route and the methods declaring it.
    exclusions: ``METHOD /path`` to the reason it is excluded.

  Returns:
    One message per problem; empty when every route is accounted for.
  """
  spec = {str(RouteKey(r.method, r.path)) for r in routes}
  owners = {str(key): names for key, names in declared.items()}
  problems: list[str] = []

  for key in sorted(spec - owners.keys() - exclusions.keys()):
    problems.append(f"{key}: in the spec, but no resource method declares it and it is not excluded")

  for key in sorted(owners.keys() - spec):
    problems.append(f"{key}: declared by {', '.join(owners[key])}, but not in the spec")

  for key in sorted(k for k, names in owners.items() if len(names) > 1):
    problems.append(f"{key}: declared by more than one method: {', '.join(owners[key])}")

  for key in sorted(exclusions.keys() - spec):
    problems.append(f"{key}: excluded, but no longer in the spec; remove the exclusion")

  for key in sorted(exclusions.keys() & owners.keys()):
    problems.append(f"{key}: excluded, but implemented by {', '.join(owners[key])}; remove the exclusion")

  for key, reason in sorted(exclusions.items()):
    if not reason.strip():
      problems.append(f"{key}: excluded with no reason")

    elif NOT_YET in reason.lower() and not re.search(r"#\d+", reason):
      problems.append(f"{key}: {NOT_YET!r} names no issue")

  return problems


# -----------------------------------------------------------------------------
def check_tree() -> list[str]:
  """Run the coverage check on the real tree, reading ``ROUTES`` live.

  Returns:
    The problems; empty when every route is accounted for.
  """
  return coverage_problems(routes_module.ROUTES, declarations(), load_exclusions())


# -----------------------------------------------------------------------------
def added_problems(
  declared: Mapping[RouteKey, Sequence[str]] | None = None,
  exclusions: Mapping[str, str] | None = None,
) -> set[str]:
  """Report what one change adds to the unchanged tree's problems.

  Each failure-path test changes one input -- ``ROUTES`` by monkeypatch,
  or the declarations or exclusions given here -- and expects exactly one
  new problem. The baseline is the spec as imported, so a real coverage
  gap fails the coverage test once, not every failure-path test beside it.

  Args:
    declared: Replaces the real declarations when given.
    exclusions: Replaces the real exclusion list when given.

  Returns:
    The problems the change introduced.
  """
  baseline = coverage_problems(IMPORTED_ROUTES, declarations(), load_exclusions())
  changed = coverage_problems(
    routes_module.ROUTES,
    declared if declared is not None else declarations(),
    exclusions if exclusions is not None else load_exclusions(),
  )

  return set(changed) - set(baseline)


# -----------------------------------------------------------------------------
class TestRouteCoverage:
  """The real routes, declarations and exclusions."""

  def test_every_route_is_implemented_or_excluded(self: TestRouteCoverage) -> None:
    """No spec route is unaccounted for, and no declaration or exclusion is stale."""
    problems = check_tree()  # act

    assert problems == []

  def test_discovery_finds_the_folders_routes(self: TestRouteCoverage) -> None:
    """Discovery reaches Folders, so a clean result is not an empty walk."""
    declared = declarations()  # act

    assert {key: names[0] for key, names in declared.items() if key in FOLDER_ROUTES} == FOLDER_ROUTES

  def test_exclusions_are_loaded(self: TestRouteCoverage) -> None:
    """The exclusion file is read, so a clean result is not an empty list."""
    exclusions = load_exclusions()  # act

    assert "POST /lock" in exclusions


# -----------------------------------------------------------------------------
class TestFailurePaths:
  """Each defect the check exists to catch makes it go red."""

  def test_an_added_spec_route_fails(self: TestFailurePaths, monkeypatch: pytest.MonkeyPatch) -> None:
    """A new upstream route, neither declared nor excluded, is reported."""
    added = Route(method="GET", path="/object/new-thing/{id}", parameters=(), summary="New.", description="")
    monkeypatch.setattr(routes_module, "ROUTES", (*routes_module.ROUTES, added))

    problems = added_problems()  # act

    assert problems == {"GET /object/new-thing/{id}: in the spec, but no resource method declares it and it is not excluded"}

  def test_a_removed_spec_route_makes_its_exclusion_stale(self: TestFailurePaths, monkeypatch: pytest.MonkeyPatch) -> None:
    """An exclusion whose route left the spec is reported."""
    kept = tuple(r for r in routes_module.ROUTES if (r.method, r.path) != ("POST", "/lock"))
    monkeypatch.setattr(routes_module, "ROUTES", kept)

    problems = added_problems()  # act

    assert problems == {"POST /lock: excluded, but no longer in the spec; remove the exclusion"}

  def test_a_removed_spec_route_makes_its_declaration_unknown(self: TestFailurePaths, monkeypatch: pytest.MonkeyPatch) -> None:
    """A declaration whose route left the spec is reported."""
    kept = tuple(r for r in routes_module.ROUTES if (r.method, r.path) != ("GET", "/list/object/folders"))
    monkeypatch.setattr(routes_module, "ROUTES", kept)

    problems = added_problems()  # act

    assert problems == {"GET /list/object/folders: declared by Folders.list, but not in the spec"}

  def test_an_implemented_route_still_excluded_fails(self: TestFailurePaths) -> None:
    """An exclusion for a route a method now declares is reported."""
    exclusions = {**load_exclusions(), "GET /object/folder/{id}": f"{NOT_YET}: #99 - test"}

    problems = added_problems(exclusions=exclusions)  # act

    assert problems == {"GET /object/folder/{id}: excluded, but implemented by Folders.get; remove the exclusion"}

  def test_a_route_declared_twice_fails(self: TestFailurePaths) -> None:
    """Two methods declaring one route are reported."""
    declared = {**declarations(), RouteKey("POST", "/object/folder"): ["Folders.add", "Other.add"]}

    problems = added_problems(declared=declared)  # act

    assert problems == {"POST /object/folder: declared by more than one method: Folders.add, Other.add"}

  def test_a_misspelled_declaration_fails(self: TestFailurePaths) -> None:
    """A declaration that is not spelled as the spec spells it is reported."""
    declared = {**declarations(), RouteKey("get", "/status"): ["Other.status"]}

    problems = added_problems(declared=declared)  # act

    assert problems == {"get /status: declared by Other.status, but not in the spec"}

  @pytest.mark.parametrize(
    ("reason", "expected"),
    [
      ("", "POST /lock: excluded with no reason"),
      ("   ", "POST /lock: excluded with no reason"),
      (NOT_YET, f"POST /lock: {NOT_YET!r} names no issue"),
      ("Not Yet Implemented", f"POST /lock: {NOT_YET!r} names no issue"),
      ("Deferred: not yet implemented upstream", f"POST /lock: {NOT_YET!r} names no issue"),
    ],
  )
  def test_an_unjustified_exclusion_fails(self: TestFailurePaths, reason: str, expected: str) -> None:
    """An exclusion must say why, and a pending one must say where."""
    exclusions = {**load_exclusions(), "POST /lock": reason}

    problems = added_problems(exclusions=exclusions)  # act

    assert problems == {expected}

  def test_a_duplicate_exclusion_key_is_refused(self: TestFailurePaths, tmp_path: Path) -> None:
    """A key listed twice is an error, not a silently dropped entry."""
    path = tmp_path / "exclusions.json"
    path.write_text('{"routes": {"POST /lock": "a", "POST /lock": "b"}}')

    with pytest.raises(ValueError, match="duplicate key"):
      load_exclusions(path)
