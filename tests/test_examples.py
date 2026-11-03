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
import logging
from pathlib import Path
import re
import sys
from typing import Any, TYPE_CHECKING

from conftest import load_recorded
import httpx
import pytest

import bw_serve_client
from bw_serve_client import ApiClient
from bw_serve_client import DefaultErrorHandler
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


# -----------------------------------------------------------------------------
#: The recorded item ``item-get`` returns, and its login's password.
ITEM = load_recorded("item-get")
ITEM_ID = ITEM["response"]["body"]["data"]["id"]
ITEM_PASSWORD = ITEM["response"]["body"]["data"]["login"]["password"]


class TestCli:
  """``examples/cli.py`` runs each command against recorded ``bw serve`` answers.

  ``connect`` stands in for ``ApiClient``: it builds a real one over an
  ``httpx.MockTransport`` that answers each path from a recording, so the
  app is exercised through its own ``main`` without a server.
  """

  @pytest.fixture
  def cli(self: TestCli) -> ModuleType:
    """Provide the example module."""
    return _load(EXAMPLES / "cli.py")

  @pytest.fixture
  def connected(self: TestCli) -> dict[str, Any]:
    """Collect the keyword arguments ``main`` passes to ``connect``."""
    return {}

  def serve(self: TestCli, connected: dict[str, Any], *responses: tuple[str, int, Any]) -> Any:
    """Build a ``connect`` whose server answers each path as given.

    Args:
      connected: Receives ``connect``'s keyword arguments.
      responses: ``(path, status, body)``; a ``None`` body refuses the connection.

    Returns:
      A stand-in for ``ApiClient``.
    """
    answers = {path: (status, body) for path, status, body in responses}

    def handler(request: httpx.Request) -> httpx.Response:
      status, body = answers[request.url.path]

      if body is None:
        raise httpx.ConnectError("Connection refused", request=request)

      return httpx.Response(status, json=body)

    def connect(**kwargs: Any) -> ApiClient:
      connected.update(kwargs)
      return ApiClient(transport=httpx.MockTransport(handler), logger=kwargs["logger"], error_handler=kwargs["error_handler"])

    return connect

  @staticmethod
  def recorded(name: str) -> tuple[str, int, Any]:
    """Answer a path the way a recording did.

    Args:
      name: The recorded case.

    Returns:
      ``(path, status, body)`` for ``serve``.
    """
    payload = load_recorded(name)
    return payload["request"]["path"], payload["response"]["status"], payload["response"]["body"]

  def test_help_lists_every_command(self: TestCli, cli: ModuleType, capsys: pytest.CaptureFixture[str]) -> None:
    """``--help`` names each command and exits 0."""
    with pytest.raises(SystemExit) as exited:
      cli.main(["--help"])

    out = capsys.readouterr().out
    assert exited.value.code == 0
    assert all(command in out for command in ("setup", "status", "folders", "items", "item"))

  def test_status_prints_the_state(
    self: TestCli, cli: ModuleType, connected: dict[str, Any], capsys: pytest.CaptureFixture[str]
  ) -> None:
    """``status`` prints the user, the server and the vault's state."""
    code = cli.main(["status"], self.serve(connected, self.recorded("status-unlocked")))  # act

    assert code == cli.EXIT_OK
    assert "fixture-recorder@example.com" in capsys.readouterr().out

  def test_url_defaults_to_bw_serves_default(
    self: TestCli, cli: ModuleType, connected: dict[str, Any], monkeypatch: pytest.MonkeyPatch
  ) -> None:
    """With no ``--url`` and no ``BW_SERVE_URL``, the app connects where ``bw serve`` listens by default."""
    monkeypatch.delenv("BW_SERVE_URL", raising=False)

    cli.main(["status"], self.serve(connected, self.recorded("status-unlocked")))  # act

    assert connected["base_url"] == "http://localhost:8087"

  def test_url_reaches_connect(self: TestCli, cli: ModuleType, connected: dict[str, Any]) -> None:
    """``--url`` is the address ``ApiClient`` is given, a socket included."""
    cli.main(["--url", "unix:///tmp/bw.sock", "status"], self.serve(connected, self.recorded("status-unlocked")))  # act

    assert connected["base_url"] == "unix:///tmp/bw.sock"

  def test_folders_lists_names(
    self: TestCli, cli: ModuleType, connected: dict[str, Any], capsys: pytest.CaptureFixture[str]
  ) -> None:
    """``folders`` prints each folder, the id-less "No Folder" included."""
    code = cli.main(["folders"], self.serve(connected, self.recorded("folders-list")))  # act

    out = capsys.readouterr().out
    assert code == cli.EXIT_OK
    assert "Renamed folder" in out
    assert "No Folder" in out

  def test_items_lists_ids_and_names(
    self: TestCli, cli: ModuleType, connected: dict[str, Any], capsys: pytest.CaptureFixture[str]
  ) -> None:
    """``items`` prints each item's id and name."""
    code = cli.main(["items"], self.serve(connected, self.recorded("items-list")))  # act

    assert code == cli.EXIT_OK
    assert f"{ITEM_ID}  Recorded login" in capsys.readouterr().out

  @pytest.fixture
  def item_with_hidden_field(self: TestCli) -> tuple[str, int, Any]:
    """Answer ``item-get``'s path with its item plus one hidden custom field."""
    path, status, body = self.recorded("item-get")
    body = json.loads(json.dumps(body))
    body["data"]["fields"] = [{"name": "pin", "value": "made-up-pin", "type": 1}]
    return path, status, body

  def test_item_masks_secrets(
    self: TestCli, cli: ModuleType, connected: dict[str, Any], item_with_hidden_field: tuple[str, int, Any],
    capsys: pytest.CaptureFixture[str]
  ) -> None:
    """``item`` prints the item with its password and hidden field masked."""
    code = cli.main(["item", ITEM_ID], self.serve(connected, item_with_hidden_field))  # act

    out = capsys.readouterr().out
    assert code == cli.EXIT_OK
    assert "someone@example.com" in out
    assert "**********" in out
    assert ITEM_PASSWORD not in out
    assert "made-up-pin" not in out

  def test_item_shows_secrets_on_request(
    self: TestCli, cli: ModuleType, connected: dict[str, Any], item_with_hidden_field: tuple[str, int, Any],
    capsys: pytest.CaptureFixture[str]
  ) -> None:
    """``--show-secrets`` prints the password and the hidden field in the clear."""
    cli.main(["item", ITEM_ID, "--show-secrets"], self.serve(connected, item_with_hidden_field))  # act

    out = capsys.readouterr().out
    assert ITEM_PASSWORD in out
    assert "made-up-pin" in out

  @pytest.mark.parametrize("command", ["status", "setup"])
  def test_no_server_prints_the_setup_steps(
    self: TestCli, cli: ModuleType, connected: dict[str, Any], command: str, capsys: pytest.CaptureFixture[str]
  ) -> None:
    """With nothing listening, the app prints the setup steps once and exits non-zero."""
    code = cli.main([command], self.serve(connected, ("/status", 0, None)))  # act

    captured = capsys.readouterr()
    assert code == cli.EXIT_NO_SERVER
    assert (captured.out + captured.err).count("bw serve --hostname unix://") == 1
    assert "Step 3 is missing" in captured.err

  @pytest.mark.parametrize("verbose", [[], ["--verbose"]])
  def test_locked_vault_points_at_bw_unlock(
    self: TestCli, cli: ModuleType, connected: dict[str, Any], verbose: list[str], capsys: pytest.CaptureFixture[str]
  ) -> None:
    """A locked vault is reported with ``bw unlock``, whether the error is raised or returned."""
    code = cli.main([*verbose, "folders"], self.serve(connected, self.recorded("folders-list-locked")))  # act

    err = capsys.readouterr().err
    assert code == cli.EXIT_LOCKED
    assert "Vault is locked" in err
    assert "bw unlock" in err

  @pytest.mark.parametrize(("state", "code_name", "missing"), [
    ("status-unlocked", "EXIT_OK", "All set"),
    ("status-locked", "EXIT_LOCKED", "Step 2 is missing"),
  ])
  def test_setup_says_which_step_is_missing(
    self: TestCli, cli: ModuleType, connected: dict[str, Any], state: str, code_name: str, missing: str,
    capsys: pytest.CaptureFixture[str]
  ) -> None:
    """``setup`` prints the steps, then names the one still to do."""
    code = cli.main(["setup"], self.serve(connected, self.recorded(state)))  # act

    captured = capsys.readouterr()
    assert code == getattr(cli, code_name)
    assert "bw login" in captured.out
    assert missing in captured.out + captured.err

  @pytest.mark.parametrize(("status", "code_name", "says"), [
    (403, "EXIT_INVALID", "Request refused"),
    (500, "EXIT_SERVER_ERROR", "bw serve failed"),
  ])
  def test_errors_map_to_distinct_exit_codes(
    self: TestCli, cli: ModuleType, connected: dict[str, Any], status: int, code_name: str, says: str,
    capsys: pytest.CaptureFixture[str]
  ) -> None:
    """A refused request and a failing server each get a message and their own exit status."""
    code = cli.main(["items"], self.serve(connected, ("/list/object/items", status, {"message": "boom"})))  # act

    assert code == getattr(cli, code_name)
    assert says in capsys.readouterr().err

  def test_exit_codes_are_distinct(self: TestCli, cli: ModuleType) -> None:
    """No two outcomes share a status, and none takes argparse's 2."""
    codes = [cli.EXIT_OK, cli.EXIT_NO_SERVER, cli.EXIT_LOCKED, cli.EXIT_INVALID, cli.EXIT_SERVER_ERROR]

    assert len(set(codes)) == len(codes)
    assert 2 not in codes

  def test_item_id_must_be_a_uuid(self: TestCli, cli: ModuleType, connected: dict[str, Any]) -> None:
    """An id that is not a UUID is a validation error, before any request."""
    code = cli.main(["item", "not-a-uuid"], self.serve(connected))  # act

    assert code == cli.EXIT_INVALID

  def test_verbose_injects_a_logger_and_a_handler(
    self: TestCli, cli: ModuleType, connected: dict[str, Any], caplog: pytest.LogCaptureFixture
  ) -> None:
    """``--verbose`` passes a logger, and a handler that returns user errors, and requests are logged."""
    caplog.set_level(logging.DEBUG, logger="bw-serve-cli")

    cli.main(["--verbose", "status"], self.serve(connected, self.recorded("status-unlocked")))  # act

    handler = connected["error_handler"]
    assert connected["logger"].name == "bw-serve-cli"
    assert isinstance(handler, DefaultErrorHandler)
    assert handler.error_level == logging.ERROR
    assert handler.logger is connected["logger"]
    assert any("GET request" in record.getMessage() for record in caplog.records)

  def test_quiet_injects_nothing(self: TestCli, cli: ModuleType, connected: dict[str, Any]) -> None:
    """Without ``--verbose`` the library's own defaults are used."""
    cli.main(["status"], self.serve(connected, self.recorded("status-unlocked")))  # act

    assert connected["logger"] is None
    assert connected["error_handler"] is None
