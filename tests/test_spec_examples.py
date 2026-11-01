"""The patched spec's own examples, checked against the generated models.

Every request and response example in the patched spec
(``upstream/vault-management-api-fixed.json``) becomes one case (#33),
derived from the spec rather than listed by hand, and named by operation and
status (or ``request``, plus the example's key when the spec gives several)
so a failure says where it is.

An example passes when its model validates it **and** every key it carries
lands on a field of that model. The second half is what gives the response
cases teeth: response models ignore unknown fields (#22) and every field is
optional, so any dict validates, and a field the model lacks is dropped
without a word.

The spec carries no parameter examples, so there is no parameter case. That
is asserted rather than assumed: ``TestCoverage`` goes red the moment an
example appears anywhere this module does not read.
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import json
from pathlib import Path
import re
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple, TYPE_CHECKING

import pytest

from bw_serve_client._generated import models

if TYPE_CHECKING:
  from types import ModuleType

  import pydantic


def _load_generate() -> ModuleType:
  """Load ``codegen/generate.py`` by path, under a name no other module uses.

  Loading by path leaves ``sys.path`` alone, so no bare ``generate`` module
  becomes importable for the rest of the session.

  Returns:
    The loaded module.
  """
  path = Path(__file__).resolve().parent.parent / "codegen" / "generate.py"
  spec = importlib.util.spec_from_file_location("_bw_codegen_generate_for_spec_examples", path)
  assert spec is not None
  assert spec.loader is not None
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)

  return module


generate = _load_generate()

SPEC: Dict[str, Any] = json.loads(generate.PATCHED_SPEC.read_text(encoding="utf-8"))

# Where an example sits: the keys from the spec's root to the ``example`` or
# ``examples`` key itself.
Location = Tuple[str, ...]

NO_SCHEMA = (
  "The spec gives this response no schema, so no model exists to parse it into. "
  "It is checked automatically once a spec fix adds one."
)


@dataclass(frozen=True)
class Example:
  """One example from the spec, and the model it should satisfy.

  Attributes:
      name: The case id: method, path, then the status or ``request``.
      location: Where the ``example`` / ``examples`` key sits in the spec.
      model: The generated model's name, or None when there is no schema.
      value: The example itself.
  """

  name: str
  location: Location
  model: Optional[str]
  value: Any


# -----------------------------------------------------------------------------
def _scoped_name(method: str, path: str, suffix: str) -> str:
  """Name the model datamodel-code-generator makes for an untitled schema.

  A schema with a title is named by it (``use-title-as-name``); one without
  is named after its operation, ``/object/item-collections/{id}`` PUT's body
  becoming ``ObjectItemCollectionsIdPutRequest``. A wrong guess here cannot
  pass quietly: the lookup in ``_model`` fails and names the class it wanted.

  Arguments:
      method: The HTTP method, lower case.
      path: The operation's path.
      suffix: ``Request`` for a request body.

  Returns:
      str: The class name.
  """
  words = [word[0].upper() + word[1:] for word in re.split(r"[^A-Za-z0-9]+", path) if word]
  return "".join(words) + method.capitalize() + suffix


# -----------------------------------------------------------------------------
def _model_name(schema: Optional[Dict[str, Any]], method: str, path: str, suffix: str) -> Optional[str]:
  """Name the generated model for a schema, the way codegen names it.

  Arguments:
      schema: The content's schema, possibly a reference, or None.
      method: The HTTP method, lower case.
      path: The operation's path.
      suffix: The scope suffix for an untitled schema.

  Returns:
      Optional[str]: The class name, or None when there is no schema.
  """
  if schema is None:
    return None

  resolved = schema
  ref = schema.get("$ref")
  if isinstance(ref, str) and ref.startswith(generate.SCHEMA_REF):
    resolved = SPEC["components"]["schemas"][ref[len(generate.SCHEMA_REF):]]

  title = resolved.get("title")
  return title if isinstance(title, str) else _scoped_name(method, path, suffix)


# -----------------------------------------------------------------------------
def _content_examples(content: Dict[str, Any], name: str, location: Location, model: Optional[str]) -> Iterator[Example]:
  """Yield the examples one media type carries, in either OpenAPI form.

  Arguments:
      content: The media type object.
      name: The case id so far.
      location: Where the media type object sits.
      model: The model its examples should satisfy.

  Yields:
      Example: One per ``example``, and one per entry of ``examples``.
  """
  if "example" in content:
    yield Example(name, (*location, "example"), model, content["example"])

  for key, entry in content.get("examples", {}).items():
    yield Example(f"{name} {key}", (*location, "examples"), model, entry.get("value"))


# -----------------------------------------------------------------------------
def request_examples() -> List[Example]:
  """Collect every request body example in the patched spec.

  Returns:
      List[Example]: In the spec's order.
  """
  found: List[Example] = []

  for method, path, operation in generate.operations(SPEC):
    for media, content in operation.get("requestBody", {}).get("content", {}).items():
      model = _model_name(content.get("schema"), method, path, "Request")
      location = ("paths", path, method, "requestBody", "content", media)
      found.extend(_content_examples(content, f"{method.upper()} {path} request", location, model))

  return found


# -----------------------------------------------------------------------------
def response_examples() -> List[Example]:
  """Collect every response example in the patched spec.

  Returns:
      List[Example]: In the spec's order.
  """
  found: List[Example] = []

  for method, path, operation in generate.operations(SPEC):
    for status, response in operation.get("responses", {}).items():
      for media, content in response.get("content", {}).items():
        # Only titled response schemas exist today; an untitled one stops
        # the build (generate.response_models), so the suffix is never used.
        model = _model_name(content.get("schema"), method, path, "Response")
        location = ("paths", path, method, "responses", status, "content", media)
        found.extend(_content_examples(content, f"{method.upper()} {path} {status}", location, model))

  return found


# -----------------------------------------------------------------------------
def every_example_location(node: Any, location: Location = ()) -> Set[Location]:
  """Find every ``example`` and ``examples`` key anywhere in the spec.

  Independent of the collectors above: it walks the whole document, so a
  parameter example, a schema-level example, or a form the collectors do not
  read shows up here and not there. It stops at each example key, so a key
  named ``example`` inside an example's value is not counted.

  Arguments:
      node: Any part of the spec.
      location: Where ``node`` sits.

  Returns:
      Set[Location]: Where each example key sits.
  """
  found: Set[Location] = set()

  if isinstance(node, dict):
    for key, value in node.items():
      if key in ("example", "examples"):
        found.add((*location, key))

      else:
        found |= every_example_location(value, (*location, key))

  elif isinstance(node, list):
    for index, value in enumerate(node):
      found |= every_example_location(value, (*location, str(index)))

  return found


# -----------------------------------------------------------------------------
def unread_keys(example: Any, dumped: Any, where: str = "") -> List[str]:
  """List the keys in an example that the parsed model did not keep.

  Compares the example with the model's own dump, by alias, key by key. A
  key missing from the dump had no field to land on: the model is missing a
  field, or the example misspells one.

  Arguments:
      example: The example, or a part of it.
      dumped: The model's dump at the same place.
      where: The path so far, for the message.

  Returns:
      List[str]: Each unread key's path, such as ``[0].organizationUserId``.
  """
  unread: List[str] = []

  if isinstance(example, dict) and isinstance(dumped, dict):
    for key, value in example.items():
      if key in dumped:
        unread.extend(unread_keys(value, dumped[key], f"{where}.{key}"))

      else:
        unread.append(f"{where}.{key}")

  elif isinstance(example, list) and isinstance(dumped, list):
    for index, (item, dumped_item) in enumerate(zip(example, dumped, strict=True)):
      unread.extend(unread_keys(item, dumped_item, f"{where}[{index}]"))

  return unread


# -----------------------------------------------------------------------------
def cases(examples: List[Example]) -> List[Any]:
  """Turn examples into cases, skipping only those with no schema.

  Arguments:
      examples: The collected examples.

  Returns:
      List[Any]: One ``pytest.param`` per example, with its name as the id.
  """
  return [
    pytest.param(example, id=example.name, marks=[] if example.model else [pytest.mark.skip(reason=NO_SCHEMA)])
    for example in examples
  ]


# -----------------------------------------------------------------------------
def check(example: Example) -> None:
  """Validate an example against its model and require every key be read.

  Arguments:
      example: The example; its model is not None.
  """
  assert example.model is not None
  assert hasattr(models, example.model), f"no generated model named {example.model}"
  model: type[pydantic.BaseModel] = getattr(models, example.model)

  parsed = model.model_validate(example.value)

  assert unread_keys(example.value, parsed.model_dump(mode="json", by_alias=True)) == []


class TestResponses:
  """Every response example parses into its model."""

  @pytest.mark.parametrize("example", cases(response_examples()))
  def test_example_parses(self: TestResponses, example: Example) -> None:
    """The response model accepts the example and keeps every key in it."""
    check(example)


class TestRequests:
  """Every request body example passes its model's validation."""

  @pytest.mark.parametrize("example", cases(request_examples()))
  def test_example_validates(self: TestRequests, example: Example) -> None:
    """The request model accepts the example and keeps every key in it."""
    check(example)


class TestCoverage:
  """The cases above are the spec's examples: all of them, and not none."""

  def test_every_example_in_the_spec_is_a_case(self: TestCoverage) -> None:
    """The collectors read exactly the example keys a walk of the spec finds.

    Red when an example sits where no collector looks: a parameter example,
    a schema-level one, or a new form. Add a check for it, then extend the
    collectors. The walk finding nothing at all is red too, so an emptied or
    moved spec cannot make both sides agree on zero.
    """
    walked = every_example_location(SPEC)

    collected = {example.location for example in request_examples() + response_examples()}

    assert walked
    assert collected == walked

  def test_known_examples_are_cases(self: TestCoverage) -> None:
    """Known examples of each form are collected, each with its model.

    /unlock's request uses ``example``; /object/item's uses the ``examples``
    map; /status's 200 response has a titled schema.
    """
    by_name = {example.name: example for example in request_examples() + response_examples()}

    known = ["POST /unlock request", "POST /object/item request login", "GET /status 200"]

    assert [by_name[name].model for name in known] == ["UnlockPostRequestSchema", "ItemTemplateSchema", "StatusSchema"]
