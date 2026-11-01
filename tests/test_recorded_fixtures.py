"""Run every recorded bw serve payload through the library.

The payloads in ``tests/fixtures/serve/`` were recorded against a real
``bw serve`` (``tests/fixtures/recorder/record.py``), so they are the source
of truth for response shapes. Each one is replayed through a mock transport
and must land where the library says it does: a success body parses into its
response model, and a failure reaches the error handler with the category
``category_for_status()`` assigns.

The case list is read from the directory, and
``test_every_payload_has_an_expectation`` fails in both directions -- a new
recording with no expectation here, or an expectation whose recording is
gone -- so a re-record cannot silently shrink or outgrow what is checked.

A case where the recording and the library disagree is
``xfail(strict=True)`` with the disagreement as its reason: it passes the
day the library or the spec is fixed, and then fails until the mark comes
off.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Optional, TYPE_CHECKING
from uuid import UUID

from conftest import load_recorded
from conftest import RECORDED_DIR
import pytest

from bw_serve_client._generated.models import LockUnlockSuccessSchema
from bw_serve_client._generated.models import StatusSchema
from bw_serve_client.errors import ExternalServiceError
from bw_serve_client.errors import UserError
from bw_serve_client.errors import ValidationError
from bw_serve_client.folders import Folder
from bw_serve_client.folders import Folders

if TYPE_CHECKING:
  from conftest import MakeClient
  from conftest import ReturningHandler
  from pydantic import BaseModel

  from bw_serve_client.api_client import ApiClient
  from bw_serve_client.errors import BitwardenError

Payload = dict[str, Any]

#: Every recorded case, from the files themselves rather than a list here.
RECORDED = sorted(path.stem for path in RECORDED_DIR.glob("*.json"))

# -----------------------------------------------------------------------------
# What each recording must do in the library. Every recorded case appears in
# exactly one of the four tables below.

#: Failures, and the category the error handler must receive.
FAILURES: dict[str, type[BitwardenError]] = {
  "folders-list-locked": UserError,
  "unlock-wrong-password": UserError,
  "folder-get-deleted": ValidationError,
  "folder-get-never-existed": ValidationError,
  "folder-get-not-a-uuid": ValidationError,
  "folder-create-no-body": ValidationError,
  "folder-create-malformed-json": ValidationError,
  "unknown-route": ValidationError,
  "attachment-no-file": ExternalServiceError,
}

#: Successes on routes whose spec response is a generated model.
MODELLED: dict[str, type[BaseModel]] = {
  "status-locked": StatusSchema,
  "status-unlocked": StatusSchema,
  "unlock": LockUnlockSuccessSchema,
  "lock": LockUnlockSuccessSchema,
}

#: Successes on the Folders routes, replayed through the Folders methods.
FOLDER_ROUTES = (
  "folder-create",
  "folder-create-empty-name",
  "folder-get",
  "folder-edit",
  "folder-delete",
  "folders-list",
)

#: Successes on routes the spec gives no response model, so only the
#: envelope can be checked. Each is a coverage gap, not a pass.
UNMODELLED = (
  "sync",
  "item-create",
  "item-get",
  "items-list",
  "items-list-before-sync",
)

#: Recorded behaviour the library or the spec does not match yet, by case
#: name, with the disagreement as the reason.
MISMATCHES: dict[str, str] = {}


def _cases(names: tuple[str, ...] | list[str]) -> list[Any]:
  """Parametrize over case names, marking each recorded mismatch.

  Args:
    names: The case names.

  Returns:
    One ``pytest.param`` per name, ``xfail(strict=True)`` where the name is
    in ``MISMATCHES``.
  """
  return [
    pytest.param(name, marks=pytest.mark.xfail(strict=True, reason=MISMATCHES[name])) if name in MISMATCHES else name
    for name in names
  ]


def _client(make_client: MakeClient, payload: Payload, handler: ReturningHandler) -> ApiClient:
  """Build a client that answers with the recorded response.

  Args:
    make_client: The shared client factory.
    payload: One recording.
    handler: Receives every failure instead of raising.

  Returns:
    The client.
  """
  response = payload["response"]
  body = response["body"]

  # bw serve answers some failures as plain text ("Bad Request", "Not
  # Found", "Internal Server Error"); those are recorded as strings.
  if isinstance(body, str):
    return make_client(response["status"], text_body=body, error_handler=handler)

  return make_client(response["status"], json_body=body, error_handler=handler)


# -----------------------------------------------------------------------------
class TestRecordings:
  """The recordings themselves: complete, attributed, and redacted."""

  def test_every_payload_has_an_expectation(self: TestRecordings) -> None:
    """The recorded set and the expectation tables name the same cases."""
    # Arrange
    expected = set(FAILURES) | set(MODELLED) | set(FOLDER_ROUTES) | set(UNMODELLED)

    result = set(RECORDED)

    # Assert
    # Non-empty first: a glob that found nothing would make the parametrized
    # tests below vanish, and an empty set equals nothing else here anyway.
    assert result
    assert result == expected

  @pytest.mark.parametrize("name", RECORDED)
  def test_payload_says_where_it_came_from(self: TestRecordings, name: str) -> None:
    """Each payload names its case, request, response, CLI and server."""
    result = load_recorded(name)

    # Assert
    assert result["case"] == name
    assert result["recorded"]["cli"]
    assert result["recorded"]["server"].startswith("vaultwarden/server:")
    assert result["request"]["method"] in {"GET", "POST", "PUT", "DELETE"}
    assert result["request"]["path"].startswith("/")
    assert isinstance(result["response"]["status"], int)

  def test_session_key_is_redacted(self: TestRecordings) -> None:
    """No recording carries a session key; the unlock one shows the marker."""
    # Arrange
    # The session key appears in the unlock message as BW_SESSION="<key>"
    # and after --session; anything there but the marker is a leak.
    leak = re.compile(r'BW_SESSION=\\"(?!<redacted>)|--session (?!<redacted>)')
    texts = [(RECORDED_DIR / f"{name}.json").read_text() for name in RECORDED]

    result = [name for name, text in zip(RECORDED, texts, strict=True) if leak.search(text)]

    # Assert
    assert result == []
    assert load_recorded("unlock")["response"]["body"]["data"]["raw"] == "<redacted>"


# -----------------------------------------------------------------------------
class TestFailures:
  """Recorded failures reach the error handler with the right category."""

  @pytest.mark.parametrize("name", _cases(list(FAILURES)))
  def test_maps_to_category(self: TestFailures, name: str, make_client: MakeClient, returning_handler: ReturningHandler) -> None:
    """The recorded status and message map to the expected category."""
    # Arrange
    payload = load_recorded(name)
    client = _client(make_client, payload, returning_handler)
    send: Callable[[str], Any] = getattr(client, payload["request"]["method"].lower())

    result = send(payload["request"]["path"])

    # Assert
    assert result is returning_handler.result
    assert len(returning_handler.calls) == 1
    category, _message, status_code, _cause = returning_handler.calls[0]
    assert category is FAILURES[name]
    assert status_code == payload["response"]["status"]


# -----------------------------------------------------------------------------
class TestModelledSuccesses:
  """Recorded successes parse into their generated response models."""

  @pytest.mark.parametrize("name", _cases(list(MODELLED)))
  def test_parses_into_model(self: TestModelledSuccesses, name: str) -> None:
    """The whole recorded body validates against the route's model."""
    # Arrange
    body = load_recorded(name)["response"]["body"]

    result = MODELLED[name].model_validate(body)

    # Assert
    assert result.model_dump(by_alias=True)["success"] is True

  @pytest.mark.parametrize(("name", "status"), [("status-locked", "locked"), ("status-unlocked", "unlocked")])
  def test_status_reads_the_vault_state(self: TestModelledSuccesses, name: str, status: str) -> None:
    """The parsed status carries the state the vault was recorded in."""
    # Arrange
    body = load_recorded(name)["response"]["body"]

    result = StatusSchema.model_validate(body)

    # Assert
    assert result.data is not None
    assert result.data.template is not None
    assert result.data.template.status is not None
    assert result.data.template.status.value == status


# -----------------------------------------------------------------------------
def _folder_id(payload: Payload) -> str:
  """Take the folder id from the end of the recorded request path.

  Args:
    payload: A recording of a ``/object/folder/{id}`` request.

  Returns:
    The id.
  """
  return payload["request"]["path"].rsplit("/", 1)[1]


#: How each Folders recording is replayed: the call, given the resource and
#: the recording.
FOLDER_CALLS: dict[str, Callable[[Folders, Payload], Any]] = {
  "folder-create": lambda folders, p: folders.add(p["request"]["body"]["name"]),
  "folder-create-empty-name": lambda folders, p: folders.add(p["request"]["body"]["name"]),
  "folder-get": lambda folders, p: folders.get(_folder_id(p)),
  "folder-edit": lambda folders, p: folders.modify(_folder_id(p), p["request"]["body"]["name"]),
  "folder-delete": lambda folders, p: folders.delete(_folder_id(p)),
  "folders-list": lambda folders, _p: folders.list(),  # noqa: U101 - every call takes the recording; list needs none.
}

#: A folder reduced to the fields compared: id, name, object.
FolderFields = tuple[Optional[UUID], str, str]


def _raw_fields(item: Payload) -> FolderFields:
  """Read a folder's fields straight from the recorded JSON.

  Built without :class:`Folder`, so a defect in how the library parses a
  folder shows as a mismatch instead of being reproduced on both sides.

  Args:
    item: One folder object from a recorded response body.

  Returns:
    The id as a UUID (None for the empty id of "No Folder"), the name and
    the object discriminator.
  """
  return (UUID(item["id"]) if item["id"] else None, item["name"], item["object"])


def _parsed_fields(folder: Folder) -> FolderFields:
  """Reduce a parsed folder to the fields compared.

  Args:
    folder: What a Folders method returned.

  Returns:
    Its id, name and object.
  """
  return (folder.id, folder.name, folder.object)


def _expected_folders(payload: Payload) -> Any:
  """Build what a Folders method should return for a recording.

  Args:
    payload: One Folders recording.

  Returns:
    The fields of the folder, a list of them, or None for a delete.
  """
  data = payload["response"]["body"].get("data")

  if data is None:
    return None

  if data.get("object") == "list":
    return [_raw_fields(item) for item in data["data"]]

  return _raw_fields(data)


def _returned_folders(result: Any) -> Any:
  """Reduce what a Folders method returned to the fields compared.

  Args:
    result: A :class:`Folder`, a list of them, or None.

  Returns:
    The same shape, with each folder as its fields.
  """
  if result is None:
    return None

  if isinstance(result, list):
    return [_parsed_fields(folder) for folder in result]

  return _parsed_fields(result)


class TestFolderSuccesses:
  """Recorded Folders successes come back from the Folders methods parsed."""

  @pytest.mark.parametrize("name", _cases(FOLDER_ROUTES))
  def test_method_returns_recorded_folders(
    self: TestFolderSuccesses, name: str, make_client: MakeClient, returning_handler: ReturningHandler
  ) -> None:
    """The method returns the recorded folders and reports no failure."""
    # Arrange
    payload = load_recorded(name)
    folders = Folders(_client(make_client, payload, returning_handler))

    result = FOLDER_CALLS[name](folders, payload)

    # Assert
    assert returning_handler.calls == []
    assert _returned_folders(result) == _expected_folders(payload)

  def test_created_folder_id_is_a_uuid(self: TestFolderSuccesses) -> None:
    """A created folder's recorded id is a UUID, as Folder.id declares."""
    # Arrange
    data = load_recorded("folder-create")["response"]["body"]["data"]

    result = Folder.model_validate(data)

    # Assert
    assert result.id == UUID(data["id"])


# -----------------------------------------------------------------------------
class TestUnmodelledSuccesses:
  """Successes the spec gives no response model: only the envelope is checked."""

  @pytest.mark.parametrize("name", UNMODELLED)
  def test_envelope_is_success(self: TestUnmodelledSuccesses, name: str) -> None:
    """The body is bw serve's success envelope with a data member."""
    result = load_recorded(name)["response"]

    # Assert
    assert result["status"] == 200
    assert result["body"]["success"] is True
    assert "data" in result["body"]
