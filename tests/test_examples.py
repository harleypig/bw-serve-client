"""Every public resource class has a runnable example in ``examples/``.

TESTS.md requires an example per public API surface. Nothing here talks to
``bw serve``: each example is compiled and imported, which catches a renamed
class or method, and its ``main`` is never called.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import re
from typing import TYPE_CHECKING

import pytest

import bw_serve_client
from bw_serve_client.resource import Resource

if TYPE_CHECKING:
  from types import ModuleType

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"

RESOURCE_CLASSES = sorted(
  name for name in bw_serve_client.__all__ if isinstance(cls := getattr(bw_serve_client, name), type) and issubclass(cls, Resource)
)


# -----------------------------------------------------------------------------
def _snake(name: str) -> str:
  """Spell a class name as its example's file stem: ``VaultItems`` -> ``vault_items``.

  Args:
    name: A CamelCase class name.

  Returns:
    The snake_case stem.
  """
  return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


# -----------------------------------------------------------------------------
def _load(path: Path) -> ModuleType:
  """Import an example file under a private module name.

  Args:
    path: The example script.

  Returns:
    The imported module.
  """
  spec = importlib.util.spec_from_file_location(f"_example_{path.stem}", path)
  assert spec is not None
  assert spec.loader is not None
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module


# -----------------------------------------------------------------------------
def test_resource_classes_are_found() -> None:
  """The class list is derived, so it must not come back empty."""
  assert "Folders" in RESOURCE_CLASSES


# -----------------------------------------------------------------------------
@pytest.mark.parametrize("name", RESOURCE_CLASSES)
def test_every_resource_class_has_an_example(name: str) -> None:
  """``examples/<snake_case>.py`` exists for each exported resource class."""
  assert (EXAMPLES / f"{_snake(name)}.py").is_file()


# -----------------------------------------------------------------------------
@pytest.mark.parametrize("path", sorted(EXAMPLES.glob("*.py")), ids=lambda path: path.name)
def test_example_imports(path: Path) -> None:
  """Each example imports cleanly and defines ``main`` without running it."""
  module = _load(path)

  assert callable(getattr(module, "main", None))
