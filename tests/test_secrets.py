"""The master password and the session key never leak (#30).

Each test sends a made-up secret through ``/unlock`` with logging at DEBUG,
then searches everything a caller or a log could see -- every log record,
formatted with its traceback, the raised error's string and repr, its
``__cause__`` and ``__context__`` chain including any httpx request body, and
the reprs of the models involved -- and asserts the secret is in none of it.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Iterator, Optional

import httpx
from pydantic import BaseModel
from pydantic import SecretStr
import pytest

from bw_serve_client._generated.models import LockUnlockDataSchema
from bw_serve_client._generated.models import UnlockPostRequestSchema
from bw_serve_client.api_client import ApiClient
from bw_serve_client.errors import BitwardenError
from bw_serve_client.errors import ExternalServiceError
from bw_serve_client.errors import ValidationError
from bw_serve_client.resource import Resource

# Made-up values, distinctive enough that a partial match cannot be chance.
PASSWORD = "made-up-master-pw-7Qx4"
SESSION = "made-up-session-key-Zr9pW2=="
SECRETS = (PASSWORD, SESSION)


def _unlocked() -> dict[str, Any]:
  """Build an /unlock success body in the shape bw serve sends.

  Returns:
    The body, with the session key in both ``message`` and ``raw``.
  """
  return {
    "success": True,
    "data": {
      "noColor": False,
      "object": "message",
      "title": "Your vault is now unlocked!",
      "message": f"To unlock your vault, set your session key: $ export BW_SESSION={SESSION}",
      "raw": SESSION,
    },
  }


def _client(sent: list[httpx.Request], body: Any = None, status: int = 200, refuse: bool = False) -> ApiClient:
  """Build a client whose transport records each request, then answers it.

  Args:
    sent: Gets every request, in order.
    body: The JSON response body.
    status: The response status.
    refuse: Fail every request the way a refused connection does instead.

  Returns:
    The client.
  """

  def handler(request: httpx.Request) -> httpx.Response:
    sent.append(request)

    if refuse:
      raise httpx.ConnectError("Connection refused", request=request)

    return httpx.Response(status, json=body)

  return ApiClient(transport=httpx.MockTransport(handler))


def _chain(error: Optional[BaseException]) -> Iterator[BaseException]:
  """Walk an exception and everything linked behind it.

  Args:
    error: Where to start.

  Yields:
    Each exception once, following both ``__cause__`` and ``__context__``.
  """
  seen: set[int] = set()
  pending = [error]

  while pending:
    current = pending.pop()

    if current is None or id(current) in seen:
      continue

    seen.add(id(current))
    yield current
    pending += [current.__cause__, current.__context__]


def _exposed(records: list[logging.LogRecord], error: Optional[BaseException], *objects: object) -> str:
  """Gather everything a caller or a log could see into one string.

  Args:
    records: Every captured log record.
    error: The raised error, if any.
    objects: Further objects whose str and repr are visible.

  Returns:
    The text to search for secrets.
  """
  formatter = logging.Formatter("%(name)s %(levelname)s %(message)s")
  parts = [formatter.format(record) for record in records]
  parts += [repr(record.args) for record in records]

  for link in _chain(error):
    parts += [str(link), repr(link), repr(link.args), repr(vars(link))]

    # httpx raises RuntimeError from .request when an error carries none.
    if isinstance(link, httpx.RequestError):
      try:
        parts.append(link.request.content.decode())

      except RuntimeError:
        parts.append("<no request>")

  for item in objects:
    parts += [str(item), repr(item)]

  return "\n".join(parts)


def _assert_clean(text: str) -> None:
  """Assert no secret appears in the text.

  Args:
    text: Everything gathered by ``_exposed``.
  """
  for secret in SECRETS:
    assert secret not in text


def _unlock(client: ApiClient, body: dict[str, Any]) -> Any:
  """Call /unlock the way its resource method will.

  Args:
    client: The client to send through.
    body: The request body fields.

  Returns:
    The parsed response data.
  """
  return Resource(client)._request("POST", "/unlock", body=(UnlockPostRequestSchema, body), response_type=LockUnlockDataSchema)


# -----------------------------------------------------------------------------
@pytest.fixture
def debug(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
  """Capture every log record at DEBUG and above, from every logger.

  ``caplog.records`` is read in the test, never here: pytest swaps the
  record list between the setup and call phases.
  """
  with caplog.at_level(logging.DEBUG):
    yield caplog


# -----------------------------------------------------------------------------
class TestModels:
  """The models that hold a secret never show it."""

  def test_unlock_request_hides_password(self: TestModels) -> None:
    """The /unlock body model's repr and str mask the password."""
    model = UnlockPostRequestSchema.model_validate({"password": PASSWORD})  # act

    _assert_clean(repr(model) + str(model) + model.model_dump_json())
    assert isinstance(model.password, SecretStr)
    assert model.password.get_secret_value() == PASSWORD

  def test_unlock_response_hides_session_key(self: TestModels) -> None:
    """The /unlock data model masks the session key in message and raw."""
    model = LockUnlockDataSchema.model_validate(_unlocked()["data"])  # act

    _assert_clean(repr(model) + str(model) + model.model_dump_json())
    assert model.raw is not None
    assert model.raw.get_secret_value() == SESSION


# -----------------------------------------------------------------------------
class TestUnlockSucceeds:
  """A successful unlock sends the password and returns the key, masked."""

  def test_secrets_stay_out_of_logs_and_result(self: TestUnlockSucceeds, debug: pytest.LogCaptureFixture) -> None:
    """The server gets the password in the clear; nothing else shows either secret."""
    sent: list[httpx.Request] = []

    result = _unlock(_client(sent, _unlocked()), {"password": PASSWORD})  # act

    [request] = sent
    assert json.loads(request.content) == {"password": PASSWORD}
    assert result.raw.get_secret_value() == SESSION
    assert debug.records
    _assert_clean(_exposed(debug.records, None, result))

  def test_api_client_does_not_log_the_body(self: TestUnlockSucceeds, debug: pytest.LogCaptureFixture) -> None:
    """Posting the body straight through ApiClient logs field names only."""
    sent: list[httpx.Request] = []
    client = _client(sent, _unlocked())

    client.post("/unlock", data={"password": PASSWORD})  # act

    assert any("password" in record.getMessage() for record in debug.records)
    _assert_clean(_exposed(debug.records, None))


# -----------------------------------------------------------------------------
class TestUnlockFails:
  """Every failure on the way leaves both secrets out."""

  def test_rejected_password(self: TestUnlockFails, debug: pytest.LogCaptureFixture) -> None:
    """A 400 for a wrong password raises without the password anywhere."""
    sent: list[httpx.Request] = []
    client = _client(sent, {"success": False, "message": "Invalid master password."}, status=400)

    with pytest.raises(BitwardenError) as exc_info:  # act
      _unlock(client, {"password": PASSWORD})

    _assert_clean(_exposed(debug.records, exc_info.value))

  def test_transport_failure_cause_carries_no_request(self: TestUnlockFails, debug: pytest.LogCaptureFixture) -> None:
    """A refused connection's cause is kept, but without the request body."""
    sent: list[httpx.Request] = []

    with pytest.raises(ExternalServiceError, match="Connection refused") as exc_info:  # act
      _unlock(_client(sent, refuse=True), {"password": PASSWORD})

    [request] = sent
    assert PASSWORD in request.content.decode()
    assert isinstance(exc_info.value.__cause__, httpx.ConnectError)
    assert exc_info.value.__context__ is None
    _assert_clean(_exposed(debug.records, exc_info.value))

  @pytest.mark.parametrize(
    "body",
    [{
      "pasword": PASSWORD
    }, {
      "password": PASSWORD,
      "extra": PASSWORD
    }],
    ids=["misspelled-field", "extra-field"],
  )
  def test_invalid_body(self: TestUnlockFails, debug: pytest.LogCaptureFixture, body: dict[str, Any]) -> None:
    """A body that fails validation is reported by field, not by value."""
    sent: list[httpx.Request] = []

    with pytest.raises(ValidationError, match="Extra inputs are not permitted") as exc_info:  # act
      _unlock(_client(sent, _unlocked()), body)

    assert sent == []
    _assert_clean(_exposed(debug.records, exc_info.value))

  @pytest.mark.parametrize(
    ("body", "match"),
    [
      ({
        "success": True,
        "data": SESSION
      }, "does not match"),
      ({
        "success": True,
        "raw": SESSION
      }, "no data member"),
    ],
    ids=["wrong-shape", "no-data"],
  )
  def test_unparseable_response(self: TestUnlockFails, debug: pytest.LogCaptureFixture, body: dict[str, Any], match: str) -> None:
    """A response that does not parse is reported without its content."""
    sent: list[httpx.Request] = []

    with pytest.raises(ExternalServiceError, match=match) as exc_info:  # act
      _unlock(_client(sent, body), {"password": PASSWORD})

    _assert_clean(_exposed(debug.records, exc_info.value))


# -----------------------------------------------------------------------------
class Keys(BaseModel):
  """A body with secrets nested inside a list.

  Attributes:
    keys: Secret values.
  """

  keys: list[SecretStr]


class TestSecretBodies:
  """Secrets in a request model are sent in the clear, wherever they sit."""

  def test_nested_secrets_are_sent(self: TestSecretBodies) -> None:
    """A SecretStr inside a list reaches the server as its value."""
    sent: list[httpx.Request] = []
    client = _client(sent, {"success": True, "data": None})

    Resource(client)._request("POST", "/thing", body=(Keys, {"keys": [PASSWORD, SESSION]}))  # act

    [request] = sent
    assert json.loads(request.content) == {"keys": [PASSWORD, SESSION]}
