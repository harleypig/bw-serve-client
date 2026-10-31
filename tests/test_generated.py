"""Checks on the committed generated package (bw_serve_client/_generated/)."""

from __future__ import annotations

import ast
from enum import Enum
import inspect
import json
from pathlib import Path
import sys
from typing import List, TYPE_CHECKING

import pydantic
import pytest

import bw_serve_client
from bw_serve_client import _generated
from bw_serve_client._generated import models
from bw_serve_client._generated import routes

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "codegen"))

import generate  # noqa: E402 - importable only once codegen/ is on the path.

if TYPE_CHECKING:
  from types import ModuleType

ROOT = Path(__file__).resolve().parent.parent
SPEC = json.loads((ROOT / "upstream" / "vault-management-api-fixed.json").read_text(encoding="utf-8"))


def model_classes() -> List[type]:
  """List every model class the models module exports.

  Returns:
      List[type]: The classes, enums excluded.
  """
  return [cls for cls in (getattr(models, name) for name in models.__all__) if not issubclass(cls, Enum)]


class TestPydanticV2:
  """Every generated model is a pydantic v2 model."""

  def test_every_model_is_a_v2_base_model(self: TestPydanticV2) -> None:
    """No generated class is a v1 model, a dataclass, or a plain class.

    pydantic v1's ``BaseModel`` is a separate class, not a subclass of v2's,
    so ``issubclass`` against v2's rejects it too.
    """
    for cls in model_classes():
      assert issubclass(cls, pydantic.BaseModel), cls.__name__

  def test_models_are_found(self: TestPydanticV2) -> None:
    """The check above has models to look at."""
    assert len(model_classes()) > 20


class TestExports:
  """Each generated module defines __all__, and it is complete."""

  @pytest.mark.parametrize("module", [models, routes])
  def test_all_lists_every_class(self: TestExports, module: ModuleType) -> None:
    """__all__ names every class the module defines at its top level."""
    tree = ast.parse(inspect.getsource(module))
    classes = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}

    assert classes <= set(module.__all__)

  def test_package_reexports_both_modules(self: TestExports) -> None:
    """The package exports every model and the route list."""
    assert _generated.__all__ == [*models.__all__, *routes.__all__]

  def test_package_root_exports_every_model(self: TestExports) -> None:
    """Callers import models from bw_serve_client itself, and no model shadows a hand-written export."""
    assert set(models.__all__) <= set(bw_serve_client.__all__)
    assert len(bw_serve_client.__all__) == len(set(bw_serve_client.__all__))
    assert all(getattr(bw_serve_client, name) is getattr(models, name) for name in models.__all__)


class TestStrictness:
  """Request models forbid unknown fields; response models ignore them (#22)."""

  def test_known_models(self: TestStrictness) -> None:
    """A request model rejects an unknown field, and a response model drops it."""
    with pytest.raises(pydantic.ValidationError):
      models.FolderSchema.model_validate({"name": "x", "nmae": "typo"})

    status = models.StatusSchema.model_validate({"success": True, "data": None, "added": 1})
    assert "added" not in status.model_dump()

  def test_response_models_are_the_known_ones(self: TestStrictness) -> None:
    """The classification itself, pinned, so the next test cannot pass by agreeing with a wrong one.

    A change here means the spec's responses changed: review which models
    should ignore unknown fields, then update the list.
    """
    assert generate.response_models(SPEC) == [
      "DeviceApprovalPropertiesSchema", "LockUnlockDataSchema", "LockUnlockSuccessSchema", "StatusDataSchema", "StatusSchema",
      "TemplateSchema"
    ]

  def test_every_model_follows_its_direction(self: TestStrictness) -> None:
    """Each model's extra setting matches whether only responses use it."""
    ignore = set(generate.response_models(SPEC))

    for cls in model_classes():
      if issubclass(cls, pydantic.RootModel):
        continue

      expected = "ignore" if cls.__name__ in ignore else "forbid"
      assert cls.model_config.get("extra") == expected, cls.__name__


class TestRoutes:
  """The route list matches the patched spec."""

  def test_one_route_per_operation(self: TestRoutes) -> None:
    """Every operation in the spec is a route, and nothing else is."""
    expected = [(method.upper(), path) for method, path, _ in generate.operations(SPEC)]

    assert [(route.method, route.path) for route in routes.ROUTES] == expected

  def test_text_matches_the_spec(self: TestRoutes) -> None:
    """Summaries, descriptions and parameters are the spec's."""
    for route, (_, _, operation) in zip(routes.ROUTES, generate.operations(SPEC), strict=True):
      assert route.summary == operation.get("summary", "")
      assert route.description == operation.get("description", "")
      actual = [(p.name, p.location, p.required) for p in route.parameters]
      expected = [(p["name"], p["in"], bool(p.get("required"))) for p in generate.parameters(SPEC, route.path, operation)]
      assert actual == expected
