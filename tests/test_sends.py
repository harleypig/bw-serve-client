"""Tests for the Sends domain class."""

from __future__ import annotations

from datetime import datetime
from datetime import timezone
import json
import logging
from typing import Any, TYPE_CHECKING
from uuid import UUID

from conftest import load_recorded
from pydantic import SecretStr
import pytest

from bw_serve_client._generated.models import SendSchema
from bw_serve_client.errors import ExternalServiceError
from bw_serve_client.errors import ValidationError
from bw_serve_client.sends import Sends

if TYPE_CHECKING:
  from conftest import MakeClient
  from conftest import ReturningHandler
  import httpx

SEND_ID = UUID("e3ddf71c-165d-4175-9d34-39fc88bfe073")
DELETION = datetime(2026, 11, 8, tzinfo=timezone.utc)

# Stand-ins for the values that must never surface; distinctive, so a
# substring search cannot match by accident.
PASSWORD = "pw-must-not-leak-4f1c"
KEY = "key-must-not-leak-9b2e"


def _recorded_body(case: str) -> Any:
  """Return the response body bw serve sent for one recorded case.

  Args:
    case: The recording's name.

  Returns:
    The response body.
  """
  return load_recorded(case)["response"]["body"]


def _send_body(**overrides: Any) -> dict[str, Any]:
  """Build a success body for one Send, from the send-get recording.

  Args:
    overrides: Fields of the Send to replace, by their wire names.

  Returns:
    The response body.
  """
  body = _recorded_body("send-get")
  body["data"].update(overrides)
  return body


# -----------------------------------------------------------------------------
class TestSendsAdd:
  """Tests for Sends.add."""

  def test_posts_a_text_send_and_parses_the_recorded_reply(
    self: TestSendsAdd, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """POST /object/send with a type-0 body; the reply parses into SendSchema."""
    sends = Sends(make_client(json_body=_recorded_body("send-create")))

    result = sends.add("Recorded send", "Made-up send text.", password=PASSWORD, deletion_date=DELETION)  # act

    [request] = sent
    assert request.method == "POST"
    assert request.url.path == "/object/send"
    assert json.loads(request.content) == {
      "name": "Recorded send",
      "type": 0,
      "text": {
        "text": "Made-up send text.",
        "hidden": False
      },
      "password": PASSWORD,
      "deletionDate": "2026-11-08T00:00:00Z",
      "disabled": False,
    }
    assert isinstance(result, SendSchema)
    assert result.id == SEND_ID
    assert result.password_set is True

  # Vaultwarden refuses a Send with no disabled member (the
  # send-create-no-disabled recording), so it is sent even at its default.
  def test_always_sends_disabled(self: TestSendsAdd, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """``disabled`` is in the body when the caller does not pass it."""
    sends = Sends(make_client(json_body=_recorded_body("send-create")))

    sends.add("Recorded send", "text")  # act

    [request] = sent
    assert json.loads(request.content)["disabled"] is False

  def test_sends_every_optional_field_by_its_wire_name(
    self: TestSendsAdd, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """Optional fields go out under the template's camelCase names."""
    sends = Sends(make_client(json_body=_recorded_body("send-create")))

    sends.add(
      "n",
      "t",
      hidden=True,
      notes="private",
      password=SecretStr(PASSWORD),
      expiration_date="2026-11-07T00:00:00Z",
      max_access_count=3,
      emails=["someone@example.com"],
      disabled=True,
      hide_email=True,
    )  # act

    [request] = sent
    body = json.loads(request.content)
    assert body["text"] == {"text": "t", "hidden": True}
    assert body["notes"] == "private"
    assert body["password"] == PASSWORD
    assert body["expirationDate"] == "2026-11-07T00:00:00Z"
    assert body["maxAccessCount"] == 3
    assert body["emails"] == ["someone@example.com"]
    assert body["disabled"] is True
    assert body["hideEmail"] is True

  @pytest.mark.parametrize(
    "kwargs", [
      {
        "emails": ["not-an-email"]
      },
      {
        "deletion_date": "2026-11-08T00:00:00"
      },
      {
        "max_access_count": "many"
      },
    ],
    ids=["bad-email", "naive-date", "non-integer-count"]
  )
  def test_invalid_body_is_refused_before_sending(
    self: TestSendsAdd, kwargs: dict[str, Any], make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """A body the template rejects raises ValidationError and sends nothing."""
    sends = Sends(make_client())

    with pytest.raises(ValidationError, match="invalid body"):
      sends.add("n", "t", **kwargs)

    assert sent == []

  def test_sends_no_authorization_header(self: TestSendsAdd, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """Bw serve has no endpoint auth, so no Authorization header is sent."""
    sends = Sends(make_client(json_body=_recorded_body("send-create")))

    sends.add("n", "t")  # act

    [request] = sent
    assert "authorization" not in request.headers


# -----------------------------------------------------------------------------
class TestSendsModify:
  """Tests for Sends.modify."""

  def test_puts_the_full_send_and_parses_the_recorded_reply(
    self: TestSendsModify, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """PUT /object/send/{id} with the whole template; the reply parses."""
    sends = Sends(make_client(json_body=_recorded_body("send-edit")))

    result = sends.modify(SEND_ID, "Renamed send", "Made-up send text.", hidden=True, deletion_date=DELETION)  # act

    [request] = sent
    assert request.method == "PUT"
    assert request.url.path == f"/object/send/{SEND_ID}"
    body = json.loads(request.content)
    assert body["name"] == "Renamed send"
    assert body["type"] == 0
    assert body["text"] == {"text": "Made-up send text.", "hidden": True}
    assert isinstance(result, SendSchema)
    assert result.name == "Renamed send"
    assert result.text is not None
    assert result.text.hidden is True

  def test_omitting_disabled_sends_false(self: TestSendsModify, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A modify without ``disabled`` sends false, which re-enables the Send."""
    sends = Sends(make_client(json_body=_recorded_body("send-edit")))

    sends.modify(SEND_ID, "n", "t")  # act

    [request] = sent
    assert json.loads(request.content)["disabled"] is False

  def test_accepts_string_send_id(self: TestSendsModify, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A string id is validated and formatted into the path."""
    sends = Sends(make_client(json_body=_recorded_body("send-edit")))

    sends.modify(str(SEND_ID), "n", "t")  # act

    [request] = sent
    assert request.url.path == f"/object/send/{SEND_ID}"

  def test_rejects_non_uuid_send_id(self: TestSendsModify, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A send_id that is not a UUID raises ValidationError before sending."""
    sends = Sends(make_client())

    with pytest.raises(ValidationError, match="invalid path"):
      sends.modify("not-a-uuid", "n", "t")

    assert sent == []


# -----------------------------------------------------------------------------
class TestSendsGet:
  """Tests for Sends.get."""

  def test_gets_and_parses_the_recorded_send(self: TestSendsGet, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """GET /object/send/{id} returns the recorded Send as SendSchema."""
    sends = Sends(make_client(json_body=_recorded_body("send-get")))

    result = sends.get(SEND_ID)  # act

    [request] = sent
    assert request.method == "GET"
    assert request.url.path == f"/object/send/{SEND_ID}"
    assert isinstance(result, SendSchema)
    assert result.id == SEND_ID
    assert result.access_id == "4933HBZdQXWdNDn8iL_gcw"
    assert result.emails == []

  def test_recorded_not_found_raises_validation_error(self: TestSendsGet, make_client: MakeClient) -> None:
    """Bw serve's recorded 400 "Not found." is a ValidationError with the status."""
    sends = Sends(make_client(status=400, json_body=_recorded_body("send-get-deleted")))

    with pytest.raises(ValidationError, match="Not found.") as exc_info:
      sends.get(SEND_ID)

    assert exc_info.value.status_code == 400

  def test_server_error_raises_external_service_error(self: TestSendsGet, make_client: MakeClient) -> None:
    """A 5xx is an ExternalServiceError."""
    sends = Sends(make_client(status=500, json_body={"success": False, "message": "boom"}))

    with pytest.raises(ExternalServiceError) as exc_info:
      sends.get(SEND_ID)

    assert exc_info.value.status_code == 500

  def test_returning_handler_value_replaces_the_result(
    self: TestSendsGet, make_client: MakeClient, returning_handler: ReturningHandler
  ) -> None:
    """A handler that returns has its value come back from the method."""
    client = make_client(status=400, json_body=_recorded_body("send-get-deleted"))
    sends = Sends(client, error_handler=returning_handler)

    result = sends.get(SEND_ID)  # act

    assert result is returning_handler.result
    [(category, message, status, _)] = returning_handler.calls
    assert (category, status) == (ValidationError, 400)
    assert "Not found." in message


# -----------------------------------------------------------------------------
class TestSendsDelete:
  """Tests for Sends.delete."""

  def test_deletes_and_returns_none(self: TestSendsDelete, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """DELETE /object/send/{id} returns None on the recorded success."""
    sends = Sends(make_client(json_body=_recorded_body("send-delete")))

    result = sends.delete(SEND_ID)  # act

    [request] = sent
    assert result is None
    assert request.method == "DELETE"
    assert request.url.path == f"/object/send/{SEND_ID}"


# -----------------------------------------------------------------------------
class TestSendsList:
  """Tests for Sends.list."""

  def test_lists_through_the_object_route(self: TestSendsList, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """GET /list/object/send, never the /send/list alias, parses the list."""
    sends = Sends(make_client(json_body=_recorded_body("sends-list-object")))

    result = sends.list()  # act

    [request] = sent
    assert request.url.path == "/list/object/send"
    assert request.url.query == b""
    assert [s.id for s in result] == [SEND_ID]
    assert all(isinstance(s, SendSchema) for s in result)

  def test_search_is_a_query_parameter(self: TestSendsList, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A search term is forwarded as ``search``."""
    sends = Sends(make_client(json_body=_recorded_body("sends-list-object")))

    sends.list(search="Recorded")  # act

    [request] = sent
    assert request.url.params["search"] == "Recorded"

  def test_empty_search_sends_no_query(self: TestSendsList, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """An empty search string is treated as no filter."""
    sends = Sends(make_client(json_body=_recorded_body("sends-list-object")))

    sends.list(search="")  # act

    [request] = sent
    assert request.url.query == b""

  def test_empty_list(self: TestSendsList, make_client: MakeClient) -> None:
    """A vault with no Sends lists as an empty list."""
    sends = Sends(make_client(json_body={"success": True, "data": {"object": "list", "data": []}}))

    result = sends.list()  # act

    assert result == []


# -----------------------------------------------------------------------------
class TestSendsRemovePassword:
  """Tests for Sends.remove_password."""

  def test_posts_and_parses_the_recorded_send(
    self: TestSendsRemovePassword, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """POST /send/{id}/remove-password with no body returns the Send."""
    sends = Sends(make_client(json_body=_recorded_body("send-remove-password")))

    result = sends.remove_password(SEND_ID)  # act

    [request] = sent
    assert request.method == "POST"
    assert request.url.path == f"/send/{SEND_ID}/remove-password"
    assert request.content == b""
    assert isinstance(result, SendSchema)
    assert result.password_set is False

  def test_rejects_non_uuid_send_id(self: TestSendsRemovePassword, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A send_id that is not a UUID raises ValidationError before sending."""
    sends = Sends(make_client())

    with pytest.raises(ValidationError, match="invalid path"):
      sends.remove_password("not-a-uuid")

    assert sent == []


# -----------------------------------------------------------------------------
class TestSendsSecrets:
  """The Send's password and key stay out of reprs and logs."""

  def test_returned_send_hides_key_password_and_access_url(self: TestSendsSecrets, make_client: MakeClient) -> None:
    """The parsed Send's repr and str carry no key, password or access URL."""
    access_url = f"https://vault.example/#/send/abc/{KEY}"
    body = _send_body(key=KEY, password=PASSWORD, accessUrl=access_url)
    sends = Sends(make_client(json_body=body))

    result = sends.get(SEND_ID)  # act

    assert isinstance(result, SendSchema)
    for text in (repr(result), str(result)):
      assert KEY not in text
      assert PASSWORD not in text
    assert result.key is not None
    assert result.key.get_secret_value() == KEY
    assert result.access_url is not None
    assert result.access_url.get_secret_value() == access_url

  def test_password_is_not_logged_on_success(
    self: TestSendsSecrets, make_client: MakeClient, caplog: pytest.LogCaptureFixture
  ) -> None:
    """Sending a password and receiving a key logs neither."""
    sends = Sends(make_client(json_body=_send_body(key=KEY)))

    with caplog.at_level(logging.DEBUG):  # act
      sends.add("n", "t", password=PASSWORD)

    assert caplog.records
    assert PASSWORD not in caplog.text
    assert KEY not in caplog.text

  def test_password_is_not_in_a_validation_failure(
    self: TestSendsSecrets, make_client: MakeClient, caplog: pytest.LogCaptureFixture
  ) -> None:
    """A refused body names the problem, not the password beside it."""
    sends = Sends(make_client())

    with caplog.at_level(logging.DEBUG), pytest.raises(ValidationError) as exc_info:
      sends.add("n", "t", password=PASSWORD, emails=["not-an-email"])

    assert PASSWORD not in str(exc_info.value)
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__context__ is None
    assert PASSWORD not in caplog.text


# -----------------------------------------------------------------------------
class TestSendsInit:
  """Tests for Sends construction and DI hooks."""

  def test_uses_provided_logger(self: TestSendsInit, make_client: MakeClient, caplog: pytest.LogCaptureFixture) -> None:
    """An injected logger receives the debug output."""
    sends = Sends(make_client(json_body=_recorded_body("sends-list-object")), logger=logging.getLogger("test.sends"))

    with caplog.at_level(logging.DEBUG, logger="test.sends"):  # act
      sends.list()

    assert any(r.name == "test.sends" for r in caplog.records)

  def test_falls_back_to_client_logger(self: TestSendsInit, make_client: MakeClient) -> None:
    """With no logger given, the client's is used."""
    client = make_client()

    sends = Sends(client)  # act

    assert sends.logger is client.logger
