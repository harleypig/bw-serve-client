"""Tests for the OrgCollections domain class."""

from __future__ import annotations

from collections.abc import Callable
import json
import logging
from typing import Any, TYPE_CHECKING
from uuid import UUID

from conftest import load_recorded
import pytest

from bw_serve_client._generated.models import CollectionResponseSchema
from bw_serve_client._generated.models import GroupSchema
from bw_serve_client._generated.models import ItemSchema
from bw_serve_client._generated.models import OrgCollectionSchema
from bw_serve_client.errors import ExternalServiceError
from bw_serve_client.errors import ValidationError
from bw_serve_client.org_collections import OrgCollections

if TYPE_CHECKING:
  from conftest import MakeClient
  from conftest import ReturningHandler
  import httpx

# The recorder's organization, its two collections, and the moved note.
ORG_ID = "f64481e2-dc5d-48cf-8db1-e6d5331fe910"
COLLECTION_ID = "b88b7b2c-a25d-40f7-a56f-afb8c03ccb5b"
SECOND_ID = "3f9b4010-4013-4119-b139-5ccb280339dd"
ITEM_ID = "8d798b38-2862-4b02-9071-f717ac34a7a7"
GROUP_ID = "c4e31257-f3e1-4b13-895a-ae2700f9884e"

EMPTY_LIST = {"success": True, "data": {"object": "list", "data": []}}

#: Calls one method with valid arguments.
Call = Callable[[OrgCollections], Any]

CALLS: dict[str, Call] = {
  "add": lambda c: c.add(ORG_ID, "Second collection"),
  "modify": lambda c: c.modify(SECOND_ID, ORG_ID, "Renamed collection"),
  "get": lambda c: c.get(COLLECTION_ID, ORG_ID),
  "delete": lambda c: c.delete(SECOND_ID, ORG_ID),
  "list": lambda c: c.list(ORG_ID),
  "get_collection": lambda c: c.get_collection(COLLECTION_ID),
  "move": lambda c: c.move(ITEM_ID, ORG_ID, [COLLECTION_ID]),
  "modify_item_collections": lambda c: c.modify_item_collections(ITEM_ID, [COLLECTION_ID]),
  "list_collections": lambda c: c.list_collections(),
}

#: Calls one method with an id that is not a UUID, in the path or query.
BAD_ID_CALLS: dict[str, Call] = {
  "add": lambda c: c.add("not-a-uuid", "Second collection"),
  "modify": lambda c: c.modify("not-a-uuid", ORG_ID, "Renamed collection"),
  "get": lambda c: c.get(COLLECTION_ID, "not-a-uuid"),
  "delete": lambda c: c.delete("not-a-uuid", ORG_ID),
  "list": lambda c: c.list("not-a-uuid"),
  "get_collection": lambda c: c.get_collection("not-a-uuid"),
  "move": lambda c: c.move(ITEM_ID, "not-a-uuid", [COLLECTION_ID]),
  "modify_item_collections": lambda c: c.modify_item_collections("not-a-uuid", [COLLECTION_ID]),
}


def _recorded(case: str) -> Any:
  """Return the response body of one recording.

  Args:
    case: The recording's name.

  Returns:
    The body bw serve sent.
  """
  return load_recorded(case)["response"]["body"]


def _recorded_request_body(case: str) -> Any:
  """Return the request body of one recording.

  Args:
    case: The recording's name.

  Returns:
    The body that was sent to bw serve.
  """
  return load_recorded(case)["request"]["body"]


# -----------------------------------------------------------------------------
class TestOrgCollectionsAdd:
  """Tests for OrgCollections.add."""

  def test_posts_the_recorded_body_and_parses_the_recorded_reply(
    self: TestOrgCollectionsAdd, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """The organization id goes in both the query and the body."""
    collections = OrgCollections(make_client(json_body=_recorded("org-collection-create")))

    result = collections.add(ORG_ID, "Second collection", groups=[], users=[])  # act

    [request] = sent
    assert (request.method, request.url.path) == ("POST", "/object/org-collection")
    assert dict(request.url.params) == {"organizationId": ORG_ID}
    expected = {key: value for key, value in _recorded_request_body("org-collection-create").items() if value is not None}
    assert json.loads(request.content) == expected
    assert isinstance(result, OrgCollectionSchema)
    assert (result.id, result.name, result.groups) == (UUID(SECOND_ID), "Second collection", [])

  def test_sends_access_by_wire_names(self: TestOrgCollectionsAdd, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """Groups and users, as models or mappings, go out under their aliases."""
    collections = OrgCollections(make_client(json_body=_recorded("org-collection-create")))

    collections.add(  # act
      ORG_ID,
      "Second collection",
      external_id="ext-1",
      groups=[GroupSchema.model_validate({"id": GROUP_ID, "read_only": True})],
      users=[{"id": GROUP_ID, "hidePasswords": True, "manage": False}],
    )

    [request] = sent
    body = json.loads(request.content)
    assert body["externalId"] == "ext-1"
    assert body["groups"] == [{"id": GROUP_ID, "readOnly": True}]
    assert body["users"] == [{"id": GROUP_ID, "hidePasswords": True, "manage": False}]

  def test_unknown_access_field_is_refused_before_sending(
    self: TestOrgCollectionsAdd, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """An access entry with a field bw serve does not know is a ValidationError."""
    collections = OrgCollections(make_client())

    with pytest.raises(ValidationError, match="invalid body"):
      collections.add(ORG_ID, "Second collection", groups=[{"id": GROUP_ID, "canEdit": True}])

    assert sent == []


# -----------------------------------------------------------------------------
class TestOrgCollectionsModify:
  """Tests for OrgCollections.modify."""

  def test_puts_the_recorded_body_and_parses_the_recorded_reply(
    self: TestOrgCollectionsModify, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """PUT /object/org-collection/{id}?organizationId=... with the full body."""
    collections = OrgCollections(make_client(json_body=_recorded("org-collection-edit")))

    result = collections.modify(UUID(SECOND_ID), UUID(ORG_ID), "Renamed collection", groups=[], users=[])  # act

    [request] = sent
    assert (request.method, request.url.path) == ("PUT", f"/object/org-collection/{SECOND_ID}")
    assert dict(request.url.params) == {"organizationId": ORG_ID}
    expected = {key: value for key, value in _recorded_request_body("org-collection-edit").items() if value is not None}
    assert json.loads(request.content) == expected
    assert isinstance(result, OrgCollectionSchema)
    assert result.name == "Renamed collection"

  def test_leaves_out_access_lists_not_given(
    self: TestOrgCollectionsModify, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """Only the organization and name are sent when nothing else is given."""
    collections = OrgCollections(make_client(json_body=_recorded("org-collection-edit")))

    collections.modify(SECOND_ID, ORG_ID, "Renamed collection")  # act

    [request] = sent
    assert json.loads(request.content) == {"organizationId": ORG_ID, "name": "Renamed collection"}


# -----------------------------------------------------------------------------
class TestOrgCollectionsGet:
  """Tests for OrgCollections.get."""

  def test_gets_and_parses_the_recorded_collection(
    self: TestOrgCollectionsGet, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """GET /object/org-collection/{id}?organizationId=... returns groups and users."""
    collections = OrgCollections(make_client(json_body=_recorded("org-collection-get")))

    result = collections.get(COLLECTION_ID, ORG_ID)  # act

    [request] = sent
    assert (request.method, request.url.path) == ("GET", f"/object/org-collection/{COLLECTION_ID}")
    assert dict(request.url.params) == {"organizationId": ORG_ID}
    assert isinstance(result, OrgCollectionSchema)
    assert (result.id, result.organization_id, result.users) == (UUID(COLLECTION_ID), UUID(ORG_ID), [])


# -----------------------------------------------------------------------------
class TestOrgCollectionsDelete:
  """Tests for OrgCollections.delete."""

  def test_deletes_and_returns_none(self: TestOrgCollectionsDelete, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """DELETE /object/org-collection/{id}?organizationId=... returns None."""
    collections = OrgCollections(make_client(json_body=_recorded("org-collection-delete")))

    result = collections.delete(SECOND_ID, ORG_ID)  # act

    [request] = sent
    assert result is None
    assert (request.method, request.url.path) == ("DELETE", f"/object/org-collection/{SECOND_ID}")
    assert dict(request.url.params) == {"organizationId": ORG_ID}


# -----------------------------------------------------------------------------
class TestOrgCollectionsList:
  """Tests for OrgCollections.list."""

  def test_lists_and_parses_the_recorded_collections(
    self: TestOrgCollectionsList, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """The list answers plain collections, without access lists."""
    collections = OrgCollections(make_client(json_body=_recorded("org-collections-list")))

    result = collections.list(ORG_ID)  # act

    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/list/object/org-collections")
    assert dict(request.url.params) == {"organizationId": ORG_ID}
    [collection] = result
    assert isinstance(collection, CollectionResponseSchema)
    assert (collection.id, collection.name) == (UUID(COLLECTION_ID), "Recorded collection")

  @pytest.mark.parametrize(("search", "expected"), [("Recorded", {
    "organizationId": ORG_ID,
    "search": "Recorded"
  }), ("", {
    "organizationId": ORG_ID
  })])
  def test_search_joins_the_organization_in_the_query(
    self: TestOrgCollectionsList, search: str, expected: dict[str, str], make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """A search term is a second query parameter; an empty one is left out."""
    collections = OrgCollections(make_client(json_body=EMPTY_LIST))

    collections.list(ORG_ID, search=search)  # act

    [request] = sent
    assert dict(request.url.params) == expected

  def test_recorded_missing_organization_raises_validation_error(self: TestOrgCollectionsList, make_client: MakeClient) -> None:
    """Bw serve's 400 when no organization is named surfaces as a ValidationError."""
    recorded = load_recorded("org-collections-list-no-org")["response"]
    collections = OrgCollections(make_client(status=recorded["status"], json_body=recorded["body"]))

    with pytest.raises(ValidationError, match="option is required") as exc_info:
      collections.list(ORG_ID)

    assert exc_info.value.status_code == 400


# -----------------------------------------------------------------------------
class TestOrgCollectionsGetCollection:
  """Tests for OrgCollections.get_collection."""

  def test_gets_and_parses_the_recorded_collection(
    self: TestOrgCollectionsGetCollection, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """GET /object/collection/{id} parses into CollectionResponseSchema."""
    collections = OrgCollections(make_client(json_body=_recorded("collection-get")))

    result = collections.get_collection(UUID(COLLECTION_ID))  # act

    [request] = sent
    assert (request.method, request.url.path, request.url.query) == ("GET", f"/object/collection/{COLLECTION_ID}", b"")
    assert isinstance(result, CollectionResponseSchema)
    assert (result.organization_id, result.name) == (UUID(ORG_ID), "Recorded collection")


# -----------------------------------------------------------------------------
class TestOrgCollectionsMove:
  """Tests for OrgCollections.move."""

  def test_posts_the_recorded_array_and_parses_the_recorded_item(
    self: TestOrgCollectionsMove, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """The body is a bare JSON array of collection ids; the reply is the item."""
    collections = OrgCollections(make_client(json_body=_recorded("item-move")))

    result = collections.move(ITEM_ID, ORG_ID, [UUID(COLLECTION_ID)])  # act

    [request] = sent
    assert (request.method, request.url.path) == ("POST", f"/move/{ITEM_ID}/{ORG_ID}")
    assert json.loads(request.content) == _recorded_request_body("item-move")
    assert isinstance(result, ItemSchema)
    assert (result.organization_id, result.collection_ids) == (UUID(ORG_ID), [UUID(COLLECTION_ID)])

  def test_rejects_a_collection_id_that_is_not_a_uuid(
    self: TestOrgCollectionsMove, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """Every collection id is validated, and the failure names its position."""
    collections = OrgCollections(make_client())

    with pytest.raises(ValidationError, match=r"invalid body .*: 1: "):
      collections.move(ITEM_ID, ORG_ID, [COLLECTION_ID, "not-a-uuid"])

    assert sent == []


# -----------------------------------------------------------------------------
class TestOrgCollectionsModifyItemCollections:
  """Tests for OrgCollections.modify_item_collections."""

  def test_puts_the_recorded_array_and_parses_the_recorded_item(
    self: TestOrgCollectionsModifyItemCollections, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """PUT /object/item-collections/{id} with the array; the reply is the item."""
    collections = OrgCollections(make_client(json_body=_recorded("item-collections-edit")))

    result = collections.modify_item_collections(ITEM_ID, [COLLECTION_ID, SECOND_ID])  # act

    [request] = sent
    assert (request.method, request.url.path) == ("PUT", f"/object/item-collections/{ITEM_ID}")
    assert json.loads(request.content) == _recorded_request_body("item-collections-edit")
    assert isinstance(result, ItemSchema)
    assert set(result.collection_ids or ()) == {UUID(COLLECTION_ID), UUID(SECOND_ID)}

  def test_rejects_a_collection_id_that_is_not_a_uuid(
    self: TestOrgCollectionsModifyItemCollections, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """A malformed collection id is refused before sending."""
    collections = OrgCollections(make_client())

    with pytest.raises(ValidationError, match=r"invalid body .*: 0: "):
      collections.modify_item_collections(ITEM_ID, ["not-a-uuid"])

    assert sent == []

  def test_recorded_personal_item_raises_validation_error(
    self: TestOrgCollectionsModifyItemCollections, make_client: MakeClient
  ) -> None:
    """Bw serve's 400 for an item outside any organization."""
    recorded = load_recorded("item-collections-not-in-org")["response"]
    collections = OrgCollections(make_client(status=recorded["status"], json_body=recorded["body"]))

    with pytest.raises(ValidationError, match="does not belong to an organization"):
      collections.modify_item_collections(ITEM_ID, [COLLECTION_ID])


# -----------------------------------------------------------------------------
class TestOrgCollectionsListCollections:
  """Tests for OrgCollections.list_collections."""

  def test_lists_and_parses_the_recorded_collections(
    self: TestOrgCollectionsListCollections, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """GET /list/object/collections with no query parses every entry."""
    collections = OrgCollections(make_client(json_body=_recorded("collections-list")))

    result = collections.list_collections()  # act

    [request] = sent
    assert (request.method, request.url.path, request.url.query) == ("GET", "/list/object/collections", b"")
    assert [(c.id, c.organization_id) for c in result] == [(UUID(COLLECTION_ID), UUID(ORG_ID))]

  @pytest.mark.parametrize(("search", "expected"), [("Recorded", {"search": "Recorded"}), ("", {})])
  def test_search_is_a_query_parameter(
    self: TestOrgCollectionsListCollections, search: str, expected: dict[str, str], make_client: MakeClient,
    sent: list[httpx.Request]
  ) -> None:
    """A search term is forwarded; an empty one is left out."""
    collections = OrgCollections(make_client(json_body=EMPTY_LIST))

    collections.list_collections(search=search)  # act

    [request] = sent
    assert dict(request.url.params) == expected


# -----------------------------------------------------------------------------
class TestOrgCollectionsContract:
  """The parts of the API class contract every OrgCollections method shares."""

  @pytest.mark.parametrize("call", BAD_ID_CALLS.values(), ids=BAD_ID_CALLS.keys())
  def test_rejects_non_uuid_id(
    self: TestOrgCollectionsContract, call: Call, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """An id that is not a UUID is refused before sending."""
    collections = OrgCollections(make_client())

    with pytest.raises(ValidationError, match="invalid"):
      call(collections)

    assert sent == []

  @pytest.mark.parametrize("call", CALLS.values(), ids=CALLS.keys())
  def test_sends_no_authorization_header(
    self: TestOrgCollectionsContract, call: Call, make_client: MakeClient, sent: list[httpx.Request],
    returning_handler: ReturningHandler
  ) -> None:
    """Bw serve has no endpoint auth, so no Authorization header is sent."""
    # The reply is beside the point; the handler absorbs a reply that does
    # not parse, so one body serves every method.
    collections = OrgCollections(make_client(json_body={"success": True}), error_handler=returning_handler)

    call(collections)  # act

    [request] = sent
    assert "authorization" not in request.headers

  @pytest.mark.parametrize("call", CALLS.values(), ids=CALLS.keys())
  def test_server_error_raises_external_service_error(
    self: TestOrgCollectionsContract, call: Call, make_client: MakeClient
  ) -> None:
    """A 5xx is an ExternalServiceError carrying the status."""
    collections = OrgCollections(make_client(status=500, text_body="Internal Server Error"))

    with pytest.raises(ExternalServiceError) as exc_info:
      call(collections)

    assert exc_info.value.status_code == 500

  @pytest.mark.parametrize("call", CALLS.values(), ids=CALLS.keys())
  def test_handled_failure_returns_the_handlers_value(
    self: TestOrgCollectionsContract, call: Call, make_client: MakeClient, returning_handler: ReturningHandler
  ) -> None:
    """A handler that returns instead of raising supplies the method's result."""
    client = make_client(status=400, json_body={"success": False, "message": "Not found."})
    collections = OrgCollections(client, error_handler=returning_handler)

    result = call(collections)  # act

    assert result is returning_handler.result
    [(category, message, status_code, _cause)] = returning_handler.calls
    assert (category, message, status_code) == (ValidationError, "Not found.", 400)

  def test_handled_validation_failure_returns_the_handlers_value(
    self: TestOrgCollectionsContract, make_client: MakeClient, sent: list[httpx.Request], returning_handler: ReturningHandler
  ) -> None:
    """A refused body reaches the handler, and nothing is sent."""
    collections = OrgCollections(make_client(), error_handler=returning_handler)

    result = collections.move(ITEM_ID, ORG_ID, ["not-a-uuid"])  # act

    assert result is returning_handler.result
    [(category, _message, status_code, _cause)] = returning_handler.calls
    assert (category, status_code) == (ValidationError, None)
    assert sent == []


# -----------------------------------------------------------------------------
class TestOrgCollectionsInit:
  """Tests for OrgCollections construction and DI hooks."""

  def test_uses_provided_logger(self: TestOrgCollectionsInit, make_client: MakeClient, caplog: pytest.LogCaptureFixture) -> None:
    """Injected logger is used for debug output."""
    collections = OrgCollections(make_client(json_body=EMPTY_LIST), logger=logging.getLogger("test.collections"))

    with caplog.at_level(logging.DEBUG, logger="test.collections"):  # act
      collections.list_collections()

    assert any(r.name == "test.collections" for r in caplog.records)

  def test_falls_back_to_client_logger(self: TestOrgCollectionsInit, make_client: MakeClient) -> None:
    """When no logger is provided, the client's logger is used."""
    client = make_client()

    collections = OrgCollections(client)  # act

    assert collections.logger is client.logger
