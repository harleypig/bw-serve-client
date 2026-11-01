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

import json
from pathlib import Path
import re
from typing import Any, Callable, get_args, Optional, TYPE_CHECKING, Union
from uuid import UUID

from conftest import load_recorded
from conftest import RECORDED_DIR
from pydantic import BaseModel
from pydantic import SecretStr
import pytest
from test_spec_examples import unread_keys

from bw_serve_client._generated import models
from bw_serve_client._generated.models import CollectionListSuccessSchema
from bw_serve_client._generated.models import CollectionSuccessSchema
from bw_serve_client._generated.models import ItemListSuccessSchema
from bw_serve_client._generated.models import ItemSuccessSchema
from bw_serve_client._generated.models import LockUnlockSuccessSchema
from bw_serve_client._generated.models import OrganizationListSuccessSchema
from bw_serve_client._generated.models import OrganizationSuccessSchema
from bw_serve_client._generated.models import OrgCollectionSuccessSchema
from bw_serve_client._generated.models import OrgMemberListSuccessSchema
from bw_serve_client._generated.models import SecretStringSuccessSchema
from bw_serve_client._generated.models import SendListSuccessSchema
from bw_serve_client._generated.models import SendSuccessSchema
from bw_serve_client._generated.models import StatusSchema
from bw_serve_client._generated.models import StringSuccessSchema
from bw_serve_client._generated.models import SuccessSchema
from bw_serve_client._generated.models import SyncMessageSuccessSchema
from bw_serve_client._generated.models import TemplateSuccessSchema
from bw_serve_client.errors import ExternalServiceError
from bw_serve_client.errors import UserError
from bw_serve_client.errors import ValidationError
from bw_serve_client.folders import Folder
from bw_serve_client.folders import Folders

if TYPE_CHECKING:
  from conftest import MakeClient
  from conftest import ReturningHandler

  from bw_serve_client.api_client import ApiClient
  from bw_serve_client.errors import BitwardenError

Payload = dict[str, Any]

#: Every recorded case, from the files themselves rather than a list here.
RECORDED = sorted(path.stem for path in RECORDED_DIR.glob("*.json"))

SPEC = json.loads(
  (Path(__file__).resolve().parent.parent / "upstream" / "vault-management-api-fixed.json").read_text(encoding="utf-8")
)

# -----------------------------------------------------------------------------
# What each recording must do in the library. Every recorded case appears in
# exactly one of the four tables below: FAILURES, MODELLED, FOLDER_ROUTES and
# FILES.

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
  "item-field-never-existed": ValidationError,
  # A 400 whose body also carries "data": the ids of every matching item.
  "item-get-by-search-ambiguous": ValidationError,
  "item-archive-never-existed": ValidationError,
  "attachment-get-deleted": ValidationError,
  # Vaultwarden's 422 for the missing member, relayed as a 400 whose
  # message is the server's JSON error as a string.
  "send-create-no-disabled": ValidationError,
  "send-get-deleted": ValidationError,
  "org-collections-list-no-org": ValidationError,
  "org-members-list-unknown-org": ValidationError,
  "org-member-confirm-unknown": ValidationError,
  "item-collections-not-in-org": ValidationError,
}

#: Successes, and the generated model of the whole body: the route's 200
#: schema in the patched spec, which ``test_model_is_the_routes`` checks.
MODELLED: dict[str, type[BaseModel]] = {
  "status-locked": StatusSchema,
  "status-unlocked": StatusSchema,
  "unlock": LockUnlockSuccessSchema,
  "lock": LockUnlockSuccessSchema,
  "sync": SyncMessageSuccessSchema,
  "sync-after-move": SyncMessageSuccessSchema,
  "item-create": ItemSuccessSchema,
  "item-create-note": ItemSuccessSchema,
  "item-create-shared": ItemSuccessSchema,
  "item-get": ItemSuccessSchema,
  "item-get-by-search": ItemSuccessSchema,
  "item-edit": ItemSuccessSchema,
  "item-move": ItemSuccessSchema,
  "item-collections-edit": ItemSuccessSchema,
  "attachment-create": ItemSuccessSchema,
  "items-list": ItemListSuccessSchema,
  "items-list-before-sync": ItemListSuccessSchema,
  "items-list-archived": ItemListSuccessSchema,
  "items-list-trash": ItemListSuccessSchema,
  "item-field-username": StringSuccessSchema,
  "item-field-uri": StringSuccessSchema,
  "item-field-notes": StringSuccessSchema,
  "item-field-exposed": StringSuccessSchema,
  "fingerprint": StringSuccessSchema,
  "item-field-password": SecretStringSuccessSchema,
  "item-field-totp": SecretStringSuccessSchema,
  "generate": SecretStringSuccessSchema,
  "generate-minimums": SecretStringSuccessSchema,
  "generate-passphrase": SecretStringSuccessSchema,
  "item-archive": SuccessSchema,
  "item-restore-archived": SuccessSchema,
  "item-delete": SuccessSchema,
  "item-restore": SuccessSchema,
  "item-delete-permanent": SuccessSchema,
  "attachment-delete": SuccessSchema,
  "send-delete": SuccessSchema,
  "org-collection-delete": SuccessSchema,
  "send-create": SendSuccessSchema,
  "send-get": SendSuccessSchema,
  "send-edit": SendSuccessSchema,
  "send-remove-password": SendSuccessSchema,
  "sends-list-object": SendListSuccessSchema,
  "sends-list": SendListSuccessSchema,
  "template-item": TemplateSuccessSchema,
  "template-item-login": TemplateSuccessSchema,
  "template-folder": TemplateSuccessSchema,
  "template-org-collection": TemplateSuccessSchema,
  "template-item-collections": TemplateSuccessSchema,
  "organizations-list": OrganizationListSuccessSchema,
  "organization-get": OrganizationSuccessSchema,
  "collections-list": CollectionListSuccessSchema,
  "org-collections-list": CollectionListSuccessSchema,
  "collection-get": CollectionSuccessSchema,
  "org-collection-get": OrgCollectionSuccessSchema,
  "org-collection-create": OrgCollectionSuccessSchema,
  "org-collection-edit": OrgCollectionSuccessSchema,
  "org-members-list": OrgMemberListSuccessSchema,
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

#: Successes whose body is a file rather than JSON, with the recording that
#: uploaded it.
FILES: dict[str, str] = {
  "attachment-get": "attachment-create",
}

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


# -----------------------------------------------------------------------------
# Where a recording may hold a secret, derived from the generated models.

#: A key path from a recording's root, and the value found there.
Place = tuple[tuple[Union[str, int], ...], Any]

#: The recorder's marker for a value it removed.
REDACTED = "<redacted>"

#: Secret-typed values the recordings hold in the clear on purpose: no one's
#: secret, and each one's provenance is known.
CLEAR_ON_PURPOSE = {
  # The recorder's item-create login password and its unlock-wrong-password
  # attempt, both made up by the recorder.
  "made-up-item-password",
  "wrong-password",
  # bw's own sample login in the item.login template.
  "myp@ssword123",
  "JBSWY3DPEHPK3PXP",
}

#: Secret-typed places a recording shows in the clear on purpose, by case:
#: the TOTP code is from the recorder's made-up seed, which is redacted, and
#: expired seconds after it was recorded.
CLEAR_PLACES = {("item-field-totp", ("response", "body", "data", "data"))}

#: Names typed SecretStr that are not a secret wherever they appear: ``data``
#: is every envelope's member (the secret one is checked by model, below),
#: and ``message`` holds the session key only inside the unlock text, which
#: ``test_session_key_is_redacted`` checks.
NOT_SECRET_BY_NAME = {"data", "message"}


def _secret_names() -> set[str]:
  """Name every member a generated model types ``SecretStr``, as on the wire.

  Returns:
    The aliases (or field names) of every ``SecretStr`` member.
  """
  names: set[str] = set()

  for cls in vars(models).values():
    if not (isinstance(cls, type) and issubclass(cls, BaseModel)):
      continue

    for name, field in cls.model_fields.items():
      if SecretStr in (field.annotation, *get_args(field.annotation)):
        names.add(field.alias or name)

  return names


SECRET_NAMES = _secret_names() - NOT_SECRET_BY_NAME


def _secret_places(payload: Payload) -> list[Place]:
  """Find every place in a recording's bodies that holds a secret.

  A member named in ``SECRET_NAMES``, anywhere in the request or response
  body, and the ``data`` of a secret-string response.

  Args:
    payload: One recording.

  Returns:
    Each place, as its key path from the recording's root, and its value.
  """
  found: list[Place] = []

  def walk(node: Any, where: tuple[str | int, ...]) -> None:
    if isinstance(node, dict):
      for key, value in node.items():
        if key in SECRET_NAMES and isinstance(value, str):
          found.append(((*where, key), value))

        walk(value, (*where, key))

    elif isinstance(node, list):
      for index, value in enumerate(node):
        walk(value, (*where, index))

  walk(payload["request"]["body"], ("request", "body"))
  walk(payload["response"]["body"], ("response", "body"))

  if MODELLED.get(payload["case"]) is SecretStringSuccessSchema:
    found.append((("response", "body", "data", "data"), payload["response"]["body"]["data"]["data"]))

  return found


def _in_the_clear(name: str, value: str) -> bool:
  """Say whether a secret's value is one a recording may show.

  Args:
    name: The member's name.
    value: Its recorded value.

  Returns:
    True for the marker, an empty value, a made-up value, or a Send's
    access URL listed without its key (it ends in ``undefined`` where the
    key would be, so it carries nothing).
  """
  if value in {REDACTED, ""} or value in CLEAR_ON_PURPOSE:
    return False

  return not (name == "accessUrl" and value.endswith("/undefined"))


def _route_model(payload: Payload) -> type[BaseModel]:
  """Find the generated model of the 200 response of a recording's route.

  The recorded path is concrete, so it is matched against each spec path
  with every ``{name}`` read as one path segment.

  Args:
    payload: One recording.

  Returns:
    The model named by the route's 200 schema title.
  """
  method = payload["request"]["method"].lower()
  path = payload["request"]["path"].split("?", 1)[0]
  matches = [
    template for template, item in SPEC["paths"].items()
    if method in item and re.fullmatch(re.sub(r"\\\{[^}]+\\\}", "[^/]+", re.escape(template)), path)
  ]

  # A literal path such as /object/fingerprint/me also matches a template
  # with a parameter there; the one with fewer parameters is the route.
  [template] = sorted(matches, key=lambda candidate: candidate.count("{"))[:1]
  schema = SPEC["paths"][template][method]["responses"]["200"]["content"]["application/json"]["schema"]
  title = SPEC["components"]["schemas"][schema["$ref"].rsplit("/", 1)[1]]["title"]

  return getattr(models, title)


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
    expected = set(FAILURES) | set(MODELLED) | set(FOLDER_ROUTES) | set(FILES)

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

  def test_secret_places_are_derived(self: TestRecordings) -> None:
    """The derivation reaches the known secrets, so the check below is not vacuous."""
    places = {(name, where) for name in RECORDED for where, _ in _secret_places(load_recorded(name))}

    # Assert
    assert {"password", "totp", "key", "accessUrl", "raw", "url"} <= SECRET_NAMES
    assert ("send-edit", ("response", "body", "data", "key")) in places
    assert ("send-edit", ("response", "body", "data", "accessUrl")) in places
    assert ("generate", ("response", "body", "data", "data")) in places
    assert ("attachment-create", ("response", "body", "data", "attachments", 0, "url")) in places

  @pytest.mark.parametrize("name", RECORDED)
  def test_other_secrets_are_redacted(self: TestRecordings, name: str) -> None:
    """Every secret a recording holds shows the marker, unless made up on purpose.

    The places are derived: every member a generated model types
    ``SecretStr``, wherever it appears in either body, and the payload of
    a secret-string response. Only the places are reported, never the
    values.
    """
    places = _secret_places(load_recorded(name))

    result = [where for where, value in places if _in_the_clear(str(where[-1]), value) and (name, where) not in CLEAR_PLACES]

    # Assert
    assert result == []


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
    """The whole recorded body validates against its model and loses no key.

    Response models ignore unknown fields (#22), so validating alone would
    pass a body the model only half reads; every recorded key must land on
    a field.
    """
    # Arrange
    body = load_recorded(name)["response"]["body"]

    result = MODELLED[name].model_validate(body)

    # Assert
    dumped = result.model_dump(mode="json", by_alias=True)
    assert dumped["success"] is True
    assert unread_keys(body, dumped) == []

  @pytest.mark.parametrize("name", list(MODELLED) + list(FOLDER_ROUTES))
  def test_model_is_the_routes(self: TestModelledSuccesses, name: str) -> None:
    """Each table entry names the model the spec gives the recorded route."""
    result = _route_model(load_recorded(name))

    # Assert
    assert result is MODELLED.get(name, result)

  @pytest.mark.parametrize("name", _cases(FOLDER_ROUTES))
  def test_folder_body_parses_into_route_model(self: TestModelledSuccesses, name: str) -> None:
    """The Folders recordings also parse into the generated folder models."""
    # Arrange
    body = load_recorded(name)["response"]["body"]

    result = _route_model(load_recorded(name)).model_validate(body)

    # Assert
    assert unread_keys(body, result.model_dump(mode="json", by_alias=True)) == []

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
FolderFields = tuple[Optional[UUID], Optional[str], Optional[str]]


def _raw_fields(item: Payload) -> FolderFields:
  """Read a folder's fields straight from the recorded JSON.

  Built without :class:`Folder`, so a defect in how the library parses a
  folder shows as a mismatch instead of being reproduced on both sides.

  Args:
    item: One folder object from a recorded response body.

  Returns:
    The id as a UUID (``None`` for "No Folder"), the name and the object
    discriminator.
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
class TestFileSuccesses:
  """Successes whose body is a file: the library hands back its text."""

  @pytest.mark.parametrize("name", _cases(list(FILES)))
  def test_returns_uploaded_text(
    self: TestFileSuccesses, name: str, make_client: MakeClient, returning_handler: ReturningHandler
  ) -> None:
    """The download replays as the text the upload recording sent.

    The recorder keeps no response headers, so the replay carries no
    content type, as a file download's octet-stream would not be JSON.
    """
    # Arrange
    payload = load_recorded(name)
    uploaded = load_recorded(FILES[name])["request"]["body"]["file"]["content"]
    client = _client(make_client, payload, returning_handler)

    result = client.get(payload["request"]["path"])

    # Assert
    assert returning_handler.calls == []
    assert result == uploaded
