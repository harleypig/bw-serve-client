"""Tests for the ItemFields domain class."""

from __future__ import annotations

import logging
import traceback
from typing import Any, TYPE_CHECKING
from uuid import uuid4

from conftest import load_recorded
from pydantic import SecretStr
import pytest

from bw_serve_client.errors import ExternalServiceError
from bw_serve_client.errors import ValidationError
from bw_serve_client.item_fields import ItemFields

if TYPE_CHECKING:
  from conftest import MakeClient
  from conftest import ReturningHandler
  import httpx

# Made-up value, distinctive enough that a partial match cannot be chance.
SECRET = "made-up-field-secret-Kp3v"

PLAIN_FIELDS = ["username", "uri", "notes"]
SECRET_FIELDS = ["password", "totp"]
ALL_FIELDS = [*PLAIN_FIELDS, *SECRET_FIELDS, "exposed"]


def _string(value: Any) -> dict[str, object]:
  """Build bw serve's success body for one string field.

  Args:
    value: The field's value.

  Returns:
    The response body.
  """
  return {"success": True, "data": {"object": "string", "data": value}}


def _call(fields: ItemFields, name: str, item_id: object) -> Any:
  """Call the getter for one field.

  Args:
    fields: The resource.
    name: The field, which is also the method name.
    item_id: The item id to pass.

  Returns:
    What the getter returned.
  """
  return getattr(fields, name)(item_id)


# -----------------------------------------------------------------------------
class TestRequest:
  """Every getter sends one GET to its own route, with no body or auth."""

  @pytest.mark.parametrize("name", ALL_FIELDS)
  def test_gets_object_field_id(self: TestRequest, name: str, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """GET /object/<field>/{id}, with no body, query or authorization."""
    item_id = uuid4()
    fields = ItemFields(make_client(json_body=_string("1")))

    _call(fields, name, item_id)  # act

    [request] = sent
    assert request.method == "GET"
    assert request.url.path == f"/object/{name}/{item_id}"
    assert request.url.query == b""
    assert request.content == b""
    assert "authorization" not in request.headers

  @pytest.mark.parametrize("name", ALL_FIELDS)
  def test_accepts_string_item_id(self: TestRequest, name: str, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A UUID given as a string is passed through into the URL."""
    item_id = "3a84be8d-12e7-4223-98cd-ae0000eabdec"
    fields = ItemFields(make_client(json_body=_string("1")))

    _call(fields, name, item_id)  # act

    [request] = sent
    assert request.url.path == f"/object/{name}/{item_id}"

  # The spec types {id} as a UUID; bw get's search-term form is not offered.
  @pytest.mark.parametrize("name", ALL_FIELDS)
  @pytest.mark.parametrize("item_id", ["not-a-uuid", "example.com", ""])
  def test_rejects_non_uuid_item_id(
    self: TestRequest, name: str, item_id: str, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """An id that is not a UUID raises ValidationError before sending."""
    fields = ItemFields(make_client())

    with pytest.raises(ValidationError, match="invalid path"):
      _call(fields, name, item_id)

    assert sent == []

  @pytest.mark.parametrize("name", ALL_FIELDS)
  def test_invalid_id_goes_to_handler(
    self: TestRequest, name: str, make_client: MakeClient, returning_handler: ReturningHandler, sent: list[httpx.Request]
  ) -> None:
    """A handler that returns instead of raising supplies the result."""
    fields = ItemFields(make_client(), error_handler=returning_handler)

    result = _call(fields, name, "not-a-uuid")  # act

    [(category, _, _, _)] = returning_handler.calls
    assert result is returning_handler.result
    assert category is ValidationError
    assert sent == []


# -----------------------------------------------------------------------------
class TestRecordedResponses:
  """The recorded bw serve answers parse into each getter's return type."""

  @pytest.mark.parametrize("name", PLAIN_FIELDS)
  def test_plain_field_returns_str(self: TestRecordedResponses, name: str, make_client: MakeClient) -> None:
    """Username, URI and notes come back as the plain string recorded."""
    payload = load_recorded(f"item-field-{name}")
    fields = ItemFields(make_client(status=payload["response"]["status"], json_body=payload["response"]["body"]))

    result = _call(fields, name, uuid4())  # act

    assert type(result) is str
    assert result == payload["response"]["body"]["data"]["data"]

  @pytest.mark.parametrize("name", SECRET_FIELDS)
  def test_secret_field_returns_secret_str(self: TestRecordedResponses, name: str, make_client: MakeClient) -> None:
    """Password and TOTP come back wrapped in SecretStr."""
    payload = load_recorded(f"item-field-{name}")
    fields = ItemFields(make_client(status=payload["response"]["status"], json_body=payload["response"]["body"]))

    result = _call(fields, name, uuid4())  # act

    assert isinstance(result, SecretStr)
    assert result.get_secret_value() == payload["response"]["body"]["data"]["data"]

  def test_exposed_returns_int(self: TestRecordedResponses, make_client: MakeClient) -> None:
    """The recorded exposure count "0" comes back as the integer 0."""
    payload = load_recorded("item-field-exposed")
    fields = ItemFields(make_client(json_body=payload["response"]["body"]))

    result = fields.exposed(uuid4())  # act

    assert result == 0
    assert type(result) is int

  def test_never_existed_raises_validation_error(self: TestRecordedResponses, make_client: MakeClient) -> None:
    """Bw serve's recorded 400 "Not found." is a ValidationError with its status."""
    payload = load_recorded("item-field-never-existed")
    fields = ItemFields(make_client(status=payload["response"]["status"], json_body=payload["response"]["body"]))

    with pytest.raises(ValidationError, match="Not found.") as exc_info:
      fields.password(uuid4())

    assert exc_info.value.status_code == 400


# -----------------------------------------------------------------------------
class TestExposed:
  """The exposure count is read as an integer."""

  def test_parses_nonzero_count(self: TestExposed, make_client: MakeClient) -> None:
    """A count of "12" is 12."""
    fields = ItemFields(make_client(json_body=_string("12")))

    result = fields.exposed(uuid4())  # act

    assert result == 12

  @pytest.mark.parametrize("value", ["twelve", "", None])
  def test_non_integer_count_is_external_service_error(
    self: TestExposed, value: Any, make_client: MakeClient, returning_handler: ReturningHandler
  ) -> None:
    """A count that is not an integer is bw serve's failure, handed to the handler."""
    fields = ItemFields(make_client(json_body=_string(value)), error_handler=returning_handler)

    result = fields.exposed(uuid4())  # act

    [(category, message, _, _)] = returning_handler.calls
    assert result is returning_handler.result
    assert category is ExternalServiceError
    assert "not an integer" in message

  def test_non_integer_count_raises_by_default(self: TestExposed, make_client: MakeClient) -> None:
    """With the default handler a non-integer count raises."""
    fields = ItemFields(make_client(json_body=_string("twelve")))

    with pytest.raises(ExternalServiceError, match="not an integer"):
      fields.exposed(uuid4())


# -----------------------------------------------------------------------------
class TestStatusHandling:
  """HTTP status codes become domain errors through the error handler."""

  @pytest.mark.parametrize("name", ALL_FIELDS)
  def test_success_200_returns_value(self: TestStatusHandling, name: str, make_client: MakeClient) -> None:
    """A 200 returns the parsed value, not the envelope."""
    fields = ItemFields(make_client(json_body=_string("7")))

    result = _call(fields, name, uuid4())  # act

    assert not isinstance(result, dict)
    assert result is not None

  @pytest.mark.parametrize("name", ALL_FIELDS)
  def test_400_raises_validation_error(self: TestStatusHandling, name: str, make_client: MakeClient) -> None:
    """Bw serve's 400 is a ValidationError carrying the status."""
    fields = ItemFields(make_client(status=400, json_body={"success": False, "message": "Not found."}))

    with pytest.raises(ValidationError) as exc_info:
      _call(fields, name, uuid4())

    assert exc_info.value.status_code == 400

  @pytest.mark.parametrize("name", ALL_FIELDS)
  def test_500_raises_external_service_error(self: TestStatusHandling, name: str, make_client: MakeClient) -> None:
    """A 5xx is an ExternalServiceError carrying the status."""
    fields = ItemFields(make_client(status=500, json_body={"success": False, "message": "boom"}))

    with pytest.raises(ExternalServiceError) as exc_info:
      _call(fields, name, uuid4())

    assert exc_info.value.status_code == 500

  @pytest.mark.parametrize("name", ALL_FIELDS)
  def test_failure_goes_to_handler(
    self: TestStatusHandling, name: str, make_client: MakeClient, returning_handler: ReturningHandler
  ) -> None:
    """A handler that returns instead of raising supplies the result."""
    fields = ItemFields(
      make_client(status=400, json_body={
        "success": False,
        "message": "Not found."
      }),
      error_handler=returning_handler,
    )

    result = _call(fields, name, uuid4())  # act

    [(category, _, status_code, _)] = returning_handler.calls
    assert result is returning_handler.result
    assert category is ValidationError
    assert status_code == 400

  @pytest.mark.parametrize("name", ALL_FIELDS)
  def test_body_without_data_is_external_service_error(
    self: TestStatusHandling, name: str, make_client: MakeClient, returning_handler: ReturningHandler
  ) -> None:
    """A 200 whose body has no data member goes to the handler."""
    fields = ItemFields(make_client(json_body={"success": True}), error_handler=returning_handler)

    result = _call(fields, name, uuid4())  # act

    [(category, _, _, _)] = returning_handler.calls
    assert result is returning_handler.result
    assert category is ExternalServiceError


# -----------------------------------------------------------------------------
class TestSecretsDoNotLeak:
  """A password or TOTP code reaches no repr, str or log record."""

  @pytest.mark.parametrize("name", SECRET_FIELDS)
  def test_secret_absent_from_repr_str_and_logs(
    self: TestSecretsDoNotLeak, name: str, make_client: MakeClient, caplog: pytest.LogCaptureFixture
  ) -> None:
    """The value is reachable only through get_secret_value()."""
    fields = ItemFields(make_client(json_body=_string(SECRET)))
    caplog.set_level(logging.DEBUG)

    result = _call(fields, name, uuid4())  # act

    # Assert
    logged = "\n".join(caplog.handler.format(record) for record in caplog.records)
    assert caplog.records
    assert SECRET not in logged
    assert SECRET not in repr(result)
    assert SECRET not in str(result)
    assert SECRET not in f"{result}"
    assert result.get_secret_value() == SECRET

  @pytest.mark.parametrize("name", SECRET_FIELDS)
  def test_secret_absent_from_malformed_response_error(
    self: TestSecretsDoNotLeak, name: str, make_client: MakeClient, caplog: pytest.LogCaptureFixture
  ) -> None:
    """A response that fails to parse does not put the secret in the error."""
    body = {"success": True, "data": {"object": "not-a-string", "data": SECRET}}
    fields = ItemFields(make_client(json_body=body))

    with caplog.at_level(logging.DEBUG), pytest.raises(ExternalServiceError) as exc_info:  # act
      _call(fields, name, uuid4())

    # Assert
    logged = "\n".join(caplog.handler.format(record) for record in caplog.records)
    shown = "".join(traceback.format_exception(exc_info.value))
    assert SECRET not in logged
    assert SECRET not in shown
    assert SECRET not in repr(exc_info.value)


# -----------------------------------------------------------------------------
class TestItemFieldsInit:
  """Tests for ItemFields construction and DI hooks."""

  def test_uses_provided_logger(self: TestItemFieldsInit, make_client: MakeClient, caplog: pytest.LogCaptureFixture) -> None:
    """Injected logger is used for debug output."""
    fields = ItemFields(make_client(json_body=_string("x")), logger=logging.getLogger("test.item_fields"))

    with caplog.at_level(logging.DEBUG, logger="test.item_fields"):  # act
      fields.username(uuid4())

    assert any(r.name == "test.item_fields" for r in caplog.records)

  def test_falls_back_to_client_logger_and_handler(self: TestItemFieldsInit, make_client: MakeClient) -> None:
    """With neither given, the client's logger and error handler are used."""
    client = make_client()

    fields = ItemFields(client)  # act

    assert fields.logger is client.logger
    assert fields.error_handler is client.error_handler
