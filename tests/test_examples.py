"""Every public resource class has a runnable example in ``examples/``.

TESTS.md requires an example per public API surface. Nothing here talks to
``bw serve``: each example is compiled and imported, which catches a renamed
class or method, and its ``main`` is never called. Logic an example carries
of its own, such as how ``device_approval.py`` reads a failure, is tested
directly.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import sys
from typing import Any, TYPE_CHECKING

from conftest import load_recorded
import pytest

import bw_serve_client
from bw_serve_client.errors import ValidationError
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
def test_stdlib_names_are_found() -> None:
  """The stdlib name set is the interpreter's, so it must hold a known module."""
  assert "collections" in sys.stdlib_module_names


# -----------------------------------------------------------------------------
@pytest.mark.parametrize("path", sorted(EXAMPLES.glob("*.py")), ids=lambda path: path.name)
def test_example_does_not_shadow_stdlib(path: Path) -> None:
  """No example is named for a stdlib module.

  ``python examples/<name>.py`` puts ``examples/`` first on ``sys.path``, so
  an example named ``collections.py`` would be imported in place of the
  stdlib module it shadows. Loading by path, as ``_load`` does, cannot see
  that.
  """
  assert path.stem not in sys.stdlib_module_names


# -----------------------------------------------------------------------------
@pytest.mark.parametrize("path", sorted(EXAMPLES.glob("*.py")), ids=lambda path: path.name)
def test_example_imports(path: Path) -> None:
  """Each example imports cleanly and defines ``main`` without running it."""
  module = _load(path)

  assert callable(getattr(module, "main", None))


#: A recorded 400 relaying the server's 422, as bw serve sends it.
RELAYED = load_recorded("send-create-no-disabled")["response"]["body"]["message"]


# -----------------------------------------------------------------------------
class TestDeviceApprovalUnavailable:
  """``examples/device_approval.py`` tells an unsupported setup from other failures.

  The relayed message is the recorded shape of a server error bw serve
  passes on; only its ``statusCode`` changes between cases.
  """

  @pytest.fixture
  def unavailable(self: TestDeviceApprovalUnavailable) -> Any:
    """Provide the example's ``_unavailable``."""
    return _load(EXAMPLES / "device_approval.py")._unavailable

  def test_recording_relays_a_status(self: TestDeviceApprovalUnavailable) -> None:
    """The recorded message carries the status the cases below rewrite."""
    assert json.loads(RELAYED)["statusCode"] == 422

  def test_bw_serve_404_is_a_cli_without_the_routes(self: TestDeviceApprovalUnavailable, unavailable: Any) -> None:
    """Bw serve's own 404 means its CLI build lacks the routes."""
    result = unavailable(ValidationError("Not found", status_code=404))  # act

    assert result is not None
    assert "CLI build" in result

  @pytest.mark.parametrize("spacing", ["", " "])
  def test_relayed_404_is_a_server_without_the_endpoint(
    self: TestDeviceApprovalUnavailable, spacing: str, unavailable: Any
  ) -> None:
    """A relayed 404 means the server lacks the endpoint, however the JSON is spaced."""
    relayed = json.loads(RELAYED)
    relayed["statusCode"] = 404
    message = json.dumps(relayed, separators=(",", ":" + spacing))

    result = unavailable(ValidationError(message, status_code=400))  # act

    assert result is not None
    assert "server" in result

  @pytest.mark.parametrize("message", [RELAYED, "Not found.", "[404]", '{"statusCode": "404"}'])
  def test_other_failures_are_not_unavailability(self: TestDeviceApprovalUnavailable, message: str, unavailable: Any) -> None:
    """Any other 400 -- another relayed status, plain text, other JSON -- is not."""
    result = unavailable(ValidationError(message, status_code=400))  # act

    assert result is None
