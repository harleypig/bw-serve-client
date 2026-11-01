"""Resource method docstrings carry their route's summary and caveats from the spec.

Methods are found through ``@route``, the same discovery the route
coverage test uses. For every declared route the spec has, the docstring
must hold:

- **The summary, verbatim, as a line of its own.** For a method declaring
  one route it must be the first line -- the docstring's summary line *is*
  the spec's summary.
- **Every description paragraph after the first, verbatim.** The spec
  separates paragraphs with ``<br>``. The first paragraph restates the
  summary in wire terms ("by specifying the unique folder identifier (e.g.
  ``3a84be8d-...``) in the path"), which is noise in a Python docstring, so
  it is exempt. The later ones are the caveats a caller needs -- "Deleting
  a folder will not delete the items in it.", "Only Text Sends are
  supported." -- so they are required.

Markup is compared away on both sides: HTML tags and entities, ``**``
emphasis and backticks are dropped, en and em dashes read as ``--``, and
whitespace runs collapse, so a docstring may wrap and use RST literals.

What it does not check: the spec's tags. ``Route`` carries none, so a class
name cannot be compared with its tag. A route the spec does not have is
skipped here; the route coverage test reports it.
"""

from __future__ import annotations

import html
import inspect
import re
from typing import Any, TYPE_CHECKING

from _routes import resource_methods

from bw_serve_client._generated import routes as routes_module
from bw_serve_client._generated.routes import Route
from bw_serve_client.resource import declared_routes
from bw_serve_client.resource import route
from bw_serve_client.resource import RouteKey

if TYPE_CHECKING:
  from collections.abc import Callable, Sequence

BREAK = re.compile(r"(?:\s*<br\s*/?>\s*)+", re.IGNORECASE)


# -----------------------------------------------------------------------------
def plain(text: str) -> str:
  """Reduce spec or docstring text to words, for comparison.

  Args:
    text: Markdown and HTML from the spec, or RST from a docstring.

  Returns:
    The text without markup, with single spaces.
  """
  text = html.unescape(re.sub(r"<[^>]+>", " ", text))
  text = text.replace("–", "--").replace("—", "--")
  text = text.replace("**", "").replace("`", "")

  return " ".join(text.split())


# -----------------------------------------------------------------------------
def required_paragraphs(description: str) -> list[str]:
  """Return the description paragraphs a docstring must carry.

  Args:
    description: The spec's description.

  Returns:
    Every paragraph after the first, without markup.
  """
  return [plain(p) for p in BREAK.split(description)[1:] if plain(p)]


# -----------------------------------------------------------------------------
def docstring_problems(name: str, func: Callable[..., Any], spec: Sequence[Route]) -> list[str]:
  """Check one method's docstring against the routes it declares.

  Args:
    name: ``Class.method``, for the messages.
    func: The method.
    spec: The spec's routes.

  Returns:
    One message per problem; empty when the docstring is complete.
  """
  by_key = {RouteKey(r.method, r.path): r for r in spec}
  keys = [key for key in declared_routes(func) if key in by_key]
  doc = inspect.getdoc(func) or ""
  lines = [line.strip() for line in doc.splitlines()]
  body = plain(doc)
  problems: list[str] = []

  for key in keys:
    spec_route = by_key[key]
    summary = spec_route.summary.strip()

    if summary and summary not in lines:
      problems.append(f"{name}: docstring lacks the summary of {key}: {summary!r}")

    elif summary and len(keys) == 1 and lines[0] != summary:
      problems.append(f"{name}: docstring's first line is not the summary of {key}: {summary!r}")

    for paragraph in required_paragraphs(spec_route.description):
      if paragraph not in body:
        problems.append(f"{name}: docstring lacks a description paragraph of {key}: {paragraph!r}")

  return problems


# -----------------------------------------------------------------------------
class TestResourceDocstrings:
  """The real resource methods."""

  def test_every_docstring_carries_its_spec_text(self: TestResourceDocstrings) -> None:
    """Each declared method's docstring has its summary and caveats."""
    problems = [
      problem for cls, name, _ in resource_methods()
      for problem in docstring_problems(f"{cls.__name__}.{name}", getattr(cls, name), routes_module.ROUTES)
    ]  # act

    assert problems == []

  def test_discovery_reaches_a_method_with_a_caveat(self: TestResourceDocstrings) -> None:
    """Folders.delete is checked, and its route has a caveat to require.

    Without this, an empty walk or a spec with no later paragraphs would
    pass the check above while checking nothing.
    """
    methods = {f"{cls.__name__}.{name}": keys for cls, name, keys in resource_methods()}  # act

    assert methods["Folders.delete"] == (RouteKey("DELETE", "/object/folder/{id}"),)
    assert required_paragraphs(
      next(r for r in routes_module.ROUTES if (r.method, r.path) == ("DELETE", "/object/folder/{id}")).description
    )


# -----------------------------------------------------------------------------
SPEC = (
  Route(
    method="DELETE",
    path="/object/thing/{id}",
    parameters=(),
    summary="Delete a thing.",
    description="Delete a thing by id in the path.<br><br>Deleting a thing **will not** delete its parts &ndash; ever.",
  ),
  Route(method="GET", path="/list/object/things", parameters=(), summary="List things.", description="List things."),
  Route(method="GET", path="/things", parameters=(), summary="List things (alias).", description="An alias."),
)


# A stand-in, not a Resource subclass, so discovery never finds it.
class _Stand:
  """Methods whose docstrings exercise each rule."""

  @route("DELETE", "/object/thing/{id}")
  def complete(self: _Stand) -> None:
    """Delete a thing.

    Deleting a thing will not delete its parts -- ever.
    """

  @route("DELETE", "/object/thing/{id}")
  def rst_and_wrapped(self: _Stand) -> None:
    """Delete a thing.

    Deleting a thing **will not** delete
    its parts -- ever.
    """

  @route("DELETE", "/object/thing/{id}")
  def no_summary(self: _Stand) -> None:
    """Remove a thing.

    Deleting a thing will not delete its parts -- ever.
    """

  @route("DELETE", "/object/thing/{id}")
  def summary_not_first(self: _Stand) -> None:
    """Remove a thing.

    Delete a thing.

    Deleting a thing will not delete its parts -- ever.
    """

  @route("DELETE", "/object/thing/{id}")
  def no_caveat(self: _Stand) -> None:
    """Delete a thing."""

  @route("DELETE", "/object/thing/{id}")
  def no_docstring(self: _Stand) -> None:
    pass

  @route("GET", "/list/object/things")
  @route("GET", "/things")
  def both_summaries(self: _Stand) -> None:
    """List things.

    List things (alias).
    """

  @route("GET", "/list/object/things")
  @route("GET", "/things")
  def one_summary(self: _Stand) -> None:
    """List things."""

  @route("GET", "/not/in/spec")
  def unknown_route(self: _Stand) -> None:
    """Whatever."""


# -----------------------------------------------------------------------------
class TestDocstringRules:
  """Each rule passes a complete docstring and fails an incomplete one."""

  def test_complete_docstring_passes(self: TestDocstringRules) -> None:
    """Summary first, caveat present: no problems."""
    assert docstring_problems("S.complete", _Stand.complete, SPEC) == []

  def test_markup_and_wrapping_are_ignored(self: TestDocstringRules) -> None:
    """RST emphasis and a line break inside the caveat still match."""
    assert docstring_problems("S.rst_and_wrapped", _Stand.rst_and_wrapped, SPEC) == []

  def test_missing_summary_fails(self: TestDocstringRules) -> None:
    """A docstring without the spec's summary is reported."""
    problems = docstring_problems("S.no_summary", _Stand.no_summary, SPEC)  # act

    assert problems == ["S.no_summary: docstring lacks the summary of DELETE /object/thing/{id}: 'Delete a thing.'"]

  def test_summary_must_be_the_first_line(self: TestDocstringRules) -> None:
    """For a single route, the summary further down is not enough."""
    problems = docstring_problems("S.summary_not_first", _Stand.summary_not_first, SPEC)  # act

    assert problems == [
      "S.summary_not_first: docstring's first line is not the summary of DELETE /object/thing/{id}: 'Delete a thing.'"
    ]

  def test_missing_caveat_fails(self: TestDocstringRules) -> None:
    """A later description paragraph missing from the docstring is reported."""
    problems = docstring_problems("S.no_caveat", _Stand.no_caveat, SPEC)  # act

    assert problems == [
      "S.no_caveat: docstring lacks a description paragraph of DELETE /object/thing/{id}: "
      "'Deleting a thing will not delete its parts -- ever.'"
    ]

  def test_missing_docstring_fails(self: TestDocstringRules) -> None:
    """No docstring at all is reported, summary and caveat both."""
    problems = docstring_problems("S.no_docstring", _Stand.no_docstring, SPEC)  # act

    assert len(problems) == 2

  def test_several_routes_need_every_summary(self: TestDocstringRules) -> None:
    """A method dispatching to two routes carries both summaries, in any order."""
    assert docstring_problems("S.both_summaries", _Stand.both_summaries, SPEC) == []

  def test_several_routes_missing_one_summary_fails(self: TestDocstringRules) -> None:
    """Leaving out one of two summaries is reported."""
    problems = docstring_problems("S.one_summary", _Stand.one_summary, SPEC)  # act

    assert problems == ["S.one_summary: docstring lacks the summary of GET /things: 'List things (alias).'"]

  def test_route_not_in_spec_is_left_to_the_coverage_test(self: TestDocstringRules) -> None:
    """An unknown route raises nothing here; the coverage test reports it."""
    assert docstring_problems("S.unknown_route", _Stand.unknown_route, SPEC) == []

  def test_first_description_paragraph_is_exempt(self: TestDocstringRules) -> None:
    """Only the paragraphs after the first are required."""
    assert required_paragraphs(SPEC[0].description) == ["Deleting a thing will not delete its parts -- ever."]
