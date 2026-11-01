"""Tests for the VaultItems domain class."""

from __future__ import annotations

import json
from typing import Any, TYPE_CHECKING
from uuid import uuid4

from conftest import load_recorded
from pydantic import SecretStr
import pytest

from bw_serve_client._generated.models import ItemSchema
from bw_serve_client._generated.models import ItemTemplateSchema
from bw_serve_client.errors import ExternalServiceError
from bw_serve_client.errors import ValidationError
from bw_serve_client.vault_items import VaultItems

if TYPE_CHECKING:
  from conftest import MakeClient
  from conftest import ReturningHandler
  import httpx

ITEM_ID = "8bac0a16-5b09-4339-a78f-283b721fa073"

#: The item-get recording's login password; the recorder keeps made-up
#: values in the clear.
PASSWORD = "made-up-item-password"

NOTE = {"type": 2, "name": "Note", "secureNote": {"type": 0}}


def _response(name: str) -> Any:
  """Read the response body of one recorded case.

  Args:
    name: The case name.

  Returns:
    The recorded response body.
  """
  return load_recorded(name)["response"]["body"]


def _fetched() -> ItemSchema:
  """Parse the item-get recording, as ``get`` would have returned it.

  Returns:
    The fetched login.
  """
  return ItemSchema.model_validate(_response("item-get")["data"])


def _body(request: httpx.Request) -> Any:
  """Decode one request's JSON body.

  Args:
    request: A sent request.

  Returns:
    The decoded body.
  """
  return json.loads(request.content)


# -----------------------------------------------------------------------------
class TestAdd:
  """Tests for VaultItems.add."""

  def test_posts_fields_and_parses_item(self: TestAdd, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """POST /object/item with the fields as given; the recording parses."""
    recorded = load_recorded("item-create")
    items = VaultItems(make_client(json_body=recorded["response"]["body"]))

    result = items.add(recorded["request"]["body"])  # act

    [request] = sent
    assert request.method == "POST"
    assert request.url.path == "/object/item"
    assert "authorization" not in request.headers
    # The recorded body's "match": null is left out, as every None is.
    assert _body(request) == recorded["request"]["body"] | {
      "login": {
        "password": PASSWORD,
        "uris": [{
          "uri": "https://example.com/"
        }],
        "username": "someone@example.com",
      }
    }
    assert isinstance(result, ItemSchema)
    assert str(result.id) == ITEM_ID
    assert result.login is not None
    assert isinstance(result.login.password, SecretStr)
    assert result.login.password.get_secret_value() == PASSWORD

  def test_accepts_field_names(self: TestAdd, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """Python field names go out as the API's aliases."""
    items = VaultItems(make_client(json_body=_response("item-create-note")))
    folder_id = uuid4()

    items.add({"type": 2, "name": "Note", "secure_note": {"type": 0}, "folder_id": folder_id})  # act

    [request] = sent
    assert _body(request) == NOTE | {"folderId": str(folder_id)}

  def test_accepts_request_model(self: TestAdd, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A built ItemTemplateSchema is sent as its fields."""
    items = VaultItems(make_client(json_body=_response("item-create-note")))

    items.add(ItemTemplateSchema.model_validate(NOTE))  # act

    [request] = sent
    assert _body(request) == NOTE

  def test_fetched_item_drops_response_fields(self: TestAdd, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A fetched item is copied without its server-side fields."""
    items = VaultItems(make_client(json_body=_response("item-create")))

    items.add(_fetched())  # act

    [request] = sent
    body = _body(request)
    assert {"id", "object", "attachments", "revisionDate", "creationDate"}.isdisjoint(body)
    assert "passwordRevisionDate" not in body["login"]
    assert body["login"]["password"] == PASSWORD

  # #108 - request validation matches what bw serve accepts: with CLI
  # 2026.10.1, type 99 crashes bw serve on Vaultwarden and is stored as a
  # login on Bitwarden Cloud.
  @pytest.mark.parametrize("item_type", [0, 9, 99])
  def test_unknown_type_is_refused_before_sending(
    self: TestAdd, item_type: int, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """An unknown item type raises ValidationError and nothing is sent."""
    items = VaultItems(make_client())

    with pytest.raises(ValidationError, match=r"invalid body for POST /object/item: type: "):
      items.add({"type": item_type, "name": "Bad type"})

    assert sent == []

  def test_missing_type_is_refused(self: TestAdd, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """The type is required."""
    items = VaultItems(make_client())

    with pytest.raises(ValidationError, match=r"type: Field required"):
      items.add({"name": "No type"})

    assert sent == []

  def test_unknown_key_in_mapping_is_refused(self: TestAdd, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A mapping is not pruned: a misspelled or response-only key is refused."""
    items = VaultItems(make_client())

    with pytest.raises(ValidationError, match=r"id: Extra inputs are not permitted"):
      items.add(NOTE | {"id": ITEM_ID})

    assert sent == []

  def test_refusal_keeps_the_secret_out_of_the_message(self: TestAdd, make_client: MakeClient) -> None:
    """A refused body does not echo its values."""
    items = VaultItems(make_client())

    with pytest.raises(ValidationError) as exc_info:
      items.add({"type": 99, "login": {"password": PASSWORD}})

    assert PASSWORD not in str(exc_info.value)


# -----------------------------------------------------------------------------
class TestModify:
  """Tests for VaultItems.modify."""

  def test_get_change_put_round_trip(self: TestModify, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A fetched, changed item goes back whole, secrets included."""
    items = VaultItems(make_client(json_body=_response("item-edit")))
    changed = _fetched().model_copy(update={"name": "Renamed"})

    result = items.modify(ITEM_ID, changed)  # act

    [request] = sent
    assert request.method == "PUT"
    assert request.url.path == f"/object/item/{ITEM_ID}"
    assert "authorization" not in request.headers
    assert _body(request) == {
      "collectionIds": [],
      "favorite": False,
      "fields": [],
      "folderId": "9725df6a-c6b5-43c8-af66-875309714845",
      "login": {
        "fido2Credentials": [],
        "password": PASSWORD,
        "uris": [{
          "uri": "https://example.com/"
        }],
        "username": "someone@example.com",
      },
      "name": "Renamed",
      "notes": "Made-up item for fixture recording.",
      "passwordHistory": [],
      "reprompt": 0,
      "type": 1,
    }
    assert isinstance(result, ItemSchema)

  def test_nested_response_fields_are_dropped(self: TestModify, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A URI's checksum and a field's linkedId are not request fields."""
    items = VaultItems(make_client(json_body=_response("item-edit")))
    fetched = ItemSchema.model_validate({
      "id": ITEM_ID,
      "type": 1,
      "fields": [{
        "name": "Linked",
        "type": 3,
        "linkedId": 100
      }],
      "login": {
        "uris": [{
          "uri": "https://example.com/",
          "uriChecksum": "abc"
        }]
      },
    })

    items.modify(ITEM_ID, fetched)  # act

    [request] = sent
    assert _body(request) == {
      "type": 1,
      "fields": [{
        "name": "Linked",
        "type": 3
      }],
      "login": {
        "uris": [{
          "uri": "https://example.com/"
        }]
      },
    }

  def test_password_history_secret_survives(self: TestModify, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A secret typed SecretStr on both sides goes out in the clear."""
    items = VaultItems(make_client(json_body=_response("item-edit")))
    fetched = ItemSchema.model_validate(_response("item-edit")["data"])

    items.modify(ITEM_ID, fetched)  # act

    [request] = sent
    assert _body(request)["passwordHistory"] == [{"lastUsedDate": "2026-11-01T21:29:14.233000Z", "password": PASSWORD}]

  def test_rejects_non_uuid_item_id(self: TestModify, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """An id that is not a UUID raises ValidationError before sending."""
    items = VaultItems(make_client())

    with pytest.raises(ValidationError, match="invalid path"):
      items.modify("not-a-uuid", NOTE)

    assert sent == []


# -----------------------------------------------------------------------------
class TestGet:
  """Tests for VaultItems.get."""

  def test_gets_by_id_and_parses_item(self: TestGet, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """GET /object/item/{id}; the recording parses, its secrets wrapped."""
    items = VaultItems(make_client(json_body=_response("item-get")))

    result = items.get(ITEM_ID)  # act

    [request] = sent
    assert request.method == "GET"
    assert request.url.path == f"/object/item/{ITEM_ID}"
    assert "authorization" not in request.headers
    assert isinstance(result, ItemSchema)
    assert result.name == "Recorded login"
    assert result.login is not None
    assert isinstance(result.login.password, SecretStr)
    assert result.login.password.get_secret_value() == PASSWORD

  def test_gets_by_search_term(self: TestGet, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A search term takes the id's place in the path, as recorded."""
    recorded = load_recorded("item-get-by-search")
    items = VaultItems(make_client(json_body=recorded["response"]["body"]))

    result = items.get(search="Recorded login")  # act

    [request] = sent
    assert request.url.raw_path == recorded["request"]["path"].encode()
    assert result.name == "Recorded login"

  def test_search_term_is_quoted_whole(self: TestGet, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A slash or question mark stays inside the term."""
    items = VaultItems(make_client(json_body=_response("item-get-by-search")))

    items.get(search="a/b?c")  # act

    [request] = sent
    assert request.url.raw_path == b"/object/item/a%2Fb%3Fc"

  def test_ambiguous_search_lists_the_ids(self: TestGet, make_client: MakeClient) -> None:
    """Bw serve's 400 for two matches is a ValidationError naming both."""
    body = _response("item-get-by-search-ambiguous")
    items = VaultItems(make_client(status=400, json_body=body))

    with pytest.raises(ValidationError) as exc_info:
      items.get(search="Recorded")

    assert exc_info.value.status_code == 400
    assert all(item_id in str(exc_info.value) for item_id in body["data"])

  @pytest.mark.parametrize("arguments", [{}, {"item_id": ITEM_ID, "search": "x"}], ids=["neither", "both"])
  def test_needs_exactly_one_of_id_and_search(
    self: TestGet, arguments: dict[str, str], make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """Neither or both is refused before sending."""
    items = VaultItems(make_client())

    with pytest.raises(ValidationError, match="exactly one of item_id and search"):
      items.get(**arguments)

    assert sent == []

  def test_rejects_empty_search(self: TestGet, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """An empty term would hit /object/item/, which is not a route."""
    items = VaultItems(make_client())

    with pytest.raises(ValidationError, match="invalid path"):
      items.get(search="")

    assert sent == []

  def test_non_uuid_id_is_not_searched(self: TestGet, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """An id that is not a UUID is refused, never sent as a search."""
    items = VaultItems(make_client())

    with pytest.raises(ValidationError, match="invalid path"):
      items.get("Recorded login")

    assert sent == []


# -----------------------------------------------------------------------------
class TestDelete:
  """Tests for VaultItems.delete."""

  def test_moves_to_trash_by_default(self: TestDelete, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """DELETE /object/item/{id} with no query, as recorded; returns None."""
    recorded = load_recorded("item-delete")
    item_id = recorded["request"]["path"].rsplit("/", 1)[1]
    items = VaultItems(make_client(json_body=recorded["response"]["body"]))

    result = items.delete(item_id)  # act

    [request] = sent
    assert result is None
    assert request.method == "DELETE"
    assert request.url.raw_path == recorded["request"]["path"].encode()
    assert "authorization" not in request.headers

  def test_permanent_sends_the_flag(self: TestDelete, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """Permanent=True adds ?permanent=true, as recorded."""
    recorded = load_recorded("item-delete-permanent")
    item_id = recorded["request"]["path"].split("/")[3].split("?")[0]
    items = VaultItems(make_client(json_body=recorded["response"]["body"]))

    items.delete(item_id, permanent=True)  # act

    [request] = sent
    assert request.url.raw_path == recorded["request"]["path"].encode()


# -----------------------------------------------------------------------------
class TestRestoreAndArchive:
  """Tests for VaultItems.restore and VaultItems.archive."""

  @pytest.mark.parametrize("case", ["item-restore", "item-restore-archived"])
  def test_restore_posts_restore_item_id(
    self: TestRestoreAndArchive, case: str, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """POST /restore/item/{id}, from the trash or the archive alike."""
    recorded = load_recorded(case)
    item_id = recorded["request"]["path"].rsplit("/", 1)[1]
    items = VaultItems(make_client(json_body=recorded["response"]["body"]))

    result = items.restore(item_id)  # act

    [request] = sent
    assert result is None
    assert request.method == "POST"
    assert request.url.path == recorded["request"]["path"]
    assert request.content == b""
    assert "authorization" not in request.headers

  def test_archive_posts_archive_item_id(self: TestRestoreAndArchive, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """POST /archive/item/{id}, with ``item`` as the object type."""
    recorded = load_recorded("item-archive")
    item_id = recorded["request"]["path"].rsplit("/", 1)[1]
    items = VaultItems(make_client(json_body=recorded["response"]["body"]))

    result = items.archive(item_id)  # act

    [request] = sent
    assert result is None
    assert request.method == "POST"
    assert request.url.path == recorded["request"]["path"]
    assert "authorization" not in request.headers

  def test_archive_unknown_item_raises(self: TestRestoreAndArchive, make_client: MakeClient) -> None:
    """Bw serve's 400 "Not found." is a ValidationError carrying the status."""
    items = VaultItems(make_client(status=400, json_body=_response("item-archive-never-existed")))

    with pytest.raises(ValidationError, match="Not found.") as exc_info:
      items.archive(uuid4())

    assert exc_info.value.status_code == 400

  @pytest.mark.parametrize("method", ["restore", "archive"])
  def test_rejects_non_uuid_item_id(
    self: TestRestoreAndArchive, method: str, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """An id that is not a UUID raises ValidationError before sending."""
    items = VaultItems(make_client())

    with pytest.raises(ValidationError, match="invalid path"):
      getattr(items, method)("not-a-uuid")

    assert sent == []


# -----------------------------------------------------------------------------
class TestList:
  """Tests for VaultItems.list."""

  def test_without_filters_sends_no_query(self: TestList, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """GET /list/object/items, no query; the recording parses."""
    items = VaultItems(make_client(json_body=_response("items-list")))

    result = items.list()  # act

    [request] = sent
    assert request.method == "GET"
    assert request.url.path == "/list/object/items"
    assert request.url.query == b""
    assert "authorization" not in request.headers
    assert [item.name for item in result] == ["Recorded login"]
    assert all(isinstance(item, ItemSchema) for item in result)

  def test_every_filter_goes_out_under_the_spec_name(self: TestList, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """Each keyword maps to the spec's query parameter."""
    org, collection, folder = uuid4(), uuid4(), uuid4()
    items = VaultItems(make_client(json_body=_response("items-list-before-sync")))

    items.list(
      organization_id=org,
      collection_id=collection,
      folder_id=folder,
      url="https://example.com/",
      trash=True,
      archived=True,
      search="login",
    )  # act

    [request] = sent
    assert dict(request.url.params) == {
      "organizationId": str(org),
      "collectionId": str(collection),
      "folderid": str(folder),
      "url": "https://example.com/",
      "trash": "true",
      "archived": "true",
      "search": "login",
    }

  def test_false_flags_and_empty_search_are_left_out(self: TestList, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """Bw reads ?trash=false as a request for the trash, so it is not sent."""
    items = VaultItems(make_client(json_body=_response("items-list")))

    items.list(trash=False, archived=False, search="")  # act

    [request] = sent
    assert request.url.query == b""

  @pytest.mark.parametrize(("case", "flag"), [("items-list-trash", "trash"), ("items-list-archived", "archived")])
  def test_trash_and_archive_recordings_parse(
    self: TestList, case: str, flag: str, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """The query matches the recording, and its dated items parse."""
    recorded = load_recorded(case)
    items = VaultItems(make_client(json_body=recorded["response"]["body"]))
    flags: dict[str, Any] = {flag: True}

    [item] = items.list(**flags)  # act

    [request] = sent
    assert request.url.raw_path == recorded["request"]["path"].encode()
    assert (item.deleted_date if flag == "trash" else item.archived_date) is not None

  @pytest.mark.parametrize("keyword", ["organization_id", "collection_id", "folder_id", "url"])
  def test_rejects_malformed_filter(self: TestList, keyword: str, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A filter that is not a UUID, or not a URL, is refused before sending."""
    items = VaultItems(make_client())
    filters: dict[str, Any] = {keyword: "not valid"}

    with pytest.raises(ValidationError, match="invalid query"):
      items.list(**filters)

    assert sent == []


# -----------------------------------------------------------------------------
class TestFailures:
  """HTTP status handling and the injected error handler."""

  @pytest.mark.parametrize(("status", "category"), [(400, ValidationError), (500, ExternalServiceError)])
  def test_error_status_raises_its_category(
    self: TestFailures, status: int, category: type[Exception], make_client: MakeClient
  ) -> None:
    """A 400 is a ValidationError and a 5xx an ExternalServiceError."""
    items = VaultItems(make_client(status=status, json_body={"success": False, "message": "Boom."}))

    with pytest.raises(category, match="Boom."):
      items.get(ITEM_ID)

  def test_unparseable_response_is_external_error(self: TestFailures, make_client: MakeClient) -> None:
    """A 2xx whose data is not an item is bw serve's fault, not ours."""
    items = VaultItems(make_client(json_body={"success": True, "data": {"id": "not-a-uuid"}}))

    with pytest.raises(ExternalServiceError, match="response does not match"):
      items.get(ITEM_ID)

  def test_error_status_goes_to_handler(self: TestFailures, make_client: MakeClient, returning_handler: ReturningHandler) -> None:
    """A handler that returns instead of raising supplies the result."""
    client = make_client(status=400, json_body=_response("item-archive-never-existed"))
    items = VaultItems(client, error_handler=returning_handler)

    result = items.archive(uuid4())  # act

    [(category, message, status, _)] = returning_handler.calls
    assert result is returning_handler.result
    assert category is ValidationError
    assert status == 400
    assert "Not found." in message

  def test_validation_failure_goes_to_handler(
    self: TestFailures, make_client: MakeClient, returning_handler: ReturningHandler, sent: list[httpx.Request]
  ) -> None:
    """A refused body reaches the handler, and nothing is sent."""
    items = VaultItems(make_client(), error_handler=returning_handler)

    result = items.add({"type": 99})  # act

    [(category, _, status, _)] = returning_handler.calls
    assert result is returning_handler.result
    assert category is ValidationError
    assert status is None
    assert sent == []

  def test_id_and_search_conflict_goes_to_handler(
    self: TestFailures, make_client: MakeClient, returning_handler: ReturningHandler, sent: list[httpx.Request]
  ) -> None:
    """The get-argument check is a handled failure too, not a TypeError."""
    items = VaultItems(make_client(), error_handler=returning_handler)

    result = items.get()  # act

    assert result is returning_handler.result
    assert sent == []
