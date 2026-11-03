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
import types
from typing import Any, Callable, Iterator, Optional, Union

import httpx
from pydantic import BaseModel
from pydantic import SecretStr
import pytest

from bw_serve_client._generated import models
from bw_serve_client._generated.models import LockUnlockDataSchema
from bw_serve_client._generated.models import UnlockPostRequestSchema
from bw_serve_client.api_client import ApiClient
from bw_serve_client.errors import BitwardenError
from bw_serve_client.errors import ExternalServiceError
from bw_serve_client.errors import ValidationError
from bw_serve_client.resource import Resource
from bw_serve_client.vault_control import VaultControl
from bw_serve_client.vault_items import VaultItems

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


# -----------------------------------------------------------------------------
#: Every field that holds a secret, by model and python field name (#100,
#: #108). Each is ``format: password`` in the patched spec.
SECRET_FIELDS = [
  ("LoginResponseSchema", "password"),
  ("LoginResponseSchema", "totp"),
  ("CardResponseSchema", "number"),
  ("CardResponseSchema", "code"),
  ("PasswordHistoryResponseSchema", "password"),
  ("Fido2CredentialResponseSchema", "key_value"),
  ("SshKeyResponseSchema", "private_key"),
  ("BankAccountResponseSchema", "account_number"),
  ("BankAccountResponseSchema", "pin"),
  ("BankAccountResponseSchema", "iban"),
  ("AttachmentSchema", "url"),
  ("SendSchema", "key"),
  ("SendSchema", "access_url"),
  ("SendSchema", "password"),
  ("SecretStringResponseSchema", "data"),
  ("LockUnlockDataSchema", "raw"),
  ("PasswordHistorySchema", "password"),
  ("Fido2CredentialSchema", "key_value"),
  ("ItemSshKeySchema", "private_key"),
  ("ItemBankAccountSchema", "account_number"),
  ("ItemBankAccountSchema", "pin"),
  ("ItemBankAccountSchema", "iban"),
  ("ItemLoginSchema", "password"),
  ("ItemLoginSchema", "totp"),
  ("ItemCardSchema", "number"),
  ("ItemCardSchema", "code"),
]


class TestSecretFields:
  """Secret fields are SecretStr, so a model's repr never shows them."""

  @pytest.mark.parametrize(("model", "field"), SECRET_FIELDS)
  def test_value_is_hidden(self: TestSecretFields, model: str, field: str) -> None:
    """The field holds a SecretStr, and the model's repr does not show it."""
    cls: type[BaseModel] = getattr(models, model)

    parsed = cls.model_validate({cls.model_fields[field].alias or field: PASSWORD})  # act

    assert isinstance(getattr(parsed, field), SecretStr)
    assert PASSWORD not in repr(parsed)
    assert PASSWORD not in str(parsed)


# -----------------------------------------------------------------------------
ITEM_ID = "11111111-2222-3333-4444-555555555555"

#: Made-up item secrets (#94, #127), one per field the round trip carries.
ITEM_SECRETS = {
  "password": "made-up-login-pw-K3v8",
  "totp": "MADEUPTOTPSEED7W2Q",
  "number": "4111000011112222",
  "code": "made-up-cvv-918",
  "hidden": "made-up-hidden-field-Lq5n",
}

#: A text custom field's value, which is not a secret and stays a plain str.
TEXT_VALUE = "made-up-text-field-Pw2c"

#: A hidden custom field and a text one (#127).
CUSTOM_FIELDS = [
  {
    "name": "Recovery code",
    "value": ITEM_SECRETS["hidden"],
    "type": 1
  },
  {
    "name": "Note",
    "value": TEXT_VALUE,
    "type": 0
  },
]

#: The two generated custom-field models.
FieldModel = Union[type[models.FieldSchema], type[models.FieldResponseSchema]]

ITEMS = [
  {
    "type": 1,
    "name": "Login",
    "login": {
      "username": "someone@example.com",
      "password": ITEM_SECRETS["password"],
      "totp": ITEM_SECRETS["totp"],
    },
    "fields": CUSTOM_FIELDS,
  },
  {
    "type": 3,
    "name": "Card",
    "card": {
      "cardholderName": "Someone",
      "number": ITEM_SECRETS["number"],
      "code": ITEM_SECRETS["code"],
    },
  },
]


def _echo(sent: list[httpx.Request]) -> ApiClient:
  """Build a client whose server stores each item it is sent and returns it.

  Args:
    sent: Gets every request, in order.

  Returns:
    The client.
  """

  def handler(request: httpx.Request) -> httpx.Response:
    sent.append(request)

    item = json.loads(request.content) | {"object": "item", "id": ITEM_ID}

    return httpx.Response(200, json={"success": True, "data": item})

  return ApiClient(transport=httpx.MockTransport(handler))


# -----------------------------------------------------------------------------
class TestItemRoundTrip:
  """An item's secrets reach the server, and nothing else shows them."""

  @pytest.mark.parametrize("fields", ITEMS, ids=["login", "card"])
  def test_add_then_modify(self: TestItemRoundTrip, debug: pytest.LogCaptureFixture, fields: dict[str, Any]) -> None:
    """Add an item, then modify what came back; no repr or log shows a secret."""
    sent: list[httpx.Request] = []
    items = VaultItems(_echo(sent))
    template = models.ItemTemplateSchema.model_validate(fields)
    added = items.add(template)

    modified = items.modify(ITEM_ID, added)  # act

    assert [json.loads(request.content) for request in sent] == [fields, fields]
    assert debug.records
    text = _exposed(debug.records, None, template, added, modified)
    assert not [secret for secret in ITEM_SECRETS.values() if secret in text]


# -----------------------------------------------------------------------------
class TestHiddenFields:
  """A hidden custom field's value is a SecretStr; other fields keep a str (#127)."""

  @pytest.mark.parametrize("model", [models.FieldSchema, models.FieldResponseSchema])
  def test_hidden_value_is_masked(self: TestHiddenFields, model: FieldModel, debug: pytest.LogCaptureFixture) -> None:
    """The value is a SecretStr, readable, and in no repr, str or log record."""
    field = model.model_validate({"name": "Recovery code", "value": ITEM_SECRETS["hidden"], "type": 1})

    logging.getLogger(__name__).info("field %s / %r", field, field)  # act

    assert isinstance(field.value, SecretStr)
    assert field.value.get_secret_value() == ITEM_SECRETS["hidden"]
    assert debug.records
    assert ITEM_SECRETS["hidden"] not in _exposed(debug.records, None, field)

  @pytest.mark.parametrize("model", [models.FieldSchema, models.FieldResponseSchema])
  @pytest.mark.parametrize("kind", [0, 2, 3], ids=["text", "boolean", "linked"])
  def test_other_values_stay_plain(self: TestHiddenFields, model: FieldModel, kind: int) -> None:
    """Text, boolean and linked fields keep their value as a str."""
    field = model.model_validate({"name": "Note", "value": TEXT_VALUE, "type": kind})  # act

    assert field.value == TEXT_VALUE
    assert TEXT_VALUE in repr(field)

  def test_round_trip_keeps_both_kinds(self: TestHiddenFields) -> None:
    """After add and modify, the hidden value is masked and the text value plain."""
    sent: list[httpx.Request] = []
    items = VaultItems(_echo(sent))

    modified = items.modify(ITEM_ID, items.add(ITEMS[0]))  # act

    assert modified.fields is not None
    hidden, text = modified.fields
    assert isinstance(hidden.value, SecretStr)
    assert hidden.value.get_secret_value() == ITEM_SECRETS["hidden"]
    assert text.value == TEXT_VALUE
    assert json.loads(sent[-1].content)["fields"] == CUSTOM_FIELDS


# -----------------------------------------------------------------------------
#: How far ``_holds`` follows references out of one local.
_REACH = 6


def _holds(value: object, depth: int = 0, seen: Optional[set[int]] = None, secrets: tuple[str, ...] = (PASSWORD,)) -> bool:
  """Say whether a secret is reachable from a value.

  Follows containers and instance attributes, the way a reporter that
  serializes locals might, but stops at a ``SecretStr``: a reporter shows
  that as its mask.

  Args:
    value: A frame local, or something reachable from one.
    depth: References followed so far.
    seen: Ids already searched.
    secrets: The plaintext values to look for.

  Returns:
    True when a secret, as text or bytes, is reachable.
  """
  if isinstance(value, str):
    return any(secret in value for secret in secrets)

  if isinstance(value, (bytes, bytearray)):
    return any(secret.encode() in value for secret in secrets)

  seen = set() if seen is None else seen

  if isinstance(value, SecretStr) or depth > _REACH or id(value) in seen:
    return False

  seen.add(id(value))

  if isinstance(value, dict):
    children: list[object] = [*value.keys(), *value.values()]

  elif isinstance(value, (list, tuple, set, frozenset)):
    children = list(value)

  elif isinstance(value, (type, types.ModuleType, types.FunctionType, types.MethodType)):
    return False

  else:
    children = list(getattr(value, "__dict__", {}).values())

  return any(_holds(child, depth + 1, seen, secrets) for child in children)


def _leaking_frames(error: BaseException, secrets: tuple[str, ...] = (PASSWORD,)) -> list[str]:
  """Name every traceback frame whose locals reach a secret.

  Every exception linked to ``error`` is walked, since a reporter shows the
  frames of the whole chain.

  Args:
    error: The raised error.
    secrets: The plaintext values to look for.

  Returns:
    ``function:local`` for each local that reaches a secret.
  """
  leaks = []

  for link in _chain(error):
    tb = link.__traceback__

    while tb is not None:
      frame = tb.tb_frame
      leaks += [
        f"{frame.f_code.co_name}:{name}" for name, value in frame.f_locals.items()
        if _holds(value, secrets=secrets) or any(secret in repr(value) for secret in secrets)
      ]
      tb = tb.tb_next

  return leaks


def _answer_400(request: httpx.Request) -> httpx.Response:  # noqa: U100
  """Reject the password the way bw serve does.

  Returns:
    A 400 response.
  """
  return httpx.Response(400, json={"success": False, "message": "Invalid master password."})


class _HeldStream(httpx.SyncByteStream):
  """A response stream that keeps its request, as httpx's own transport does.

  Args:
    request: The request the response answers.
    content: The response body.
  """

  def __init__(self: _HeldStream, request: httpx.Request, content: bytes) -> None:
    self.request = request
    self.content = content

  def __iter__(self: _HeldStream) -> Iterator[bytes]:
    """Yield the body in one chunk.

    Yields:
      The response body.
    """
    yield self.content


def _answer_400_streamed(request: httpx.Request) -> httpx.Response:
  """Reject the password with a response whose stream reaches the request.

  Returns:
    A 400 response.
  """
  body = json.dumps({"success": False, "message": "Invalid master password."}).encode()

  return httpx.Response(400, headers={"Content-Type": "application/json"}, stream=_HeldStream(request, body))


def _refuse(request: httpx.Request) -> httpx.Response:
  """Fail the way a refused connection does.

  Raises:
    ConnectError: Always.
  """
  raise httpx.ConnectError("Connection refused", request=request)


def _break_mid_write(request: httpx.Request) -> httpx.Response:
  """Fail while writing the body, the way httpcore does on a dropped socket.

  The body is in a local of the frame the cause is raised in, as httpcore's
  write buffer is.

  Raises:
    OSError: Always, caught here and kept as the cause.
    WriteError: Always, from the ``OSError``.
  """
  chunk = request.read()

  try:
    raise OSError(f"Broken pipe after {len(chunk)} bytes")

  except OSError as e:
    raise httpx.WriteError("Broken pipe", request=request) from e


class TestTracebackLocals:
  """No frame on a failure's traceback holds the plaintext password (#97)."""

  @pytest.mark.parametrize(
    "answer",
    [_answer_400, _answer_400_streamed, _refuse, _break_mid_write],
    ids=["rejected", "rejected-streamed", "refused", "write-failed"],
  )
  def test_password_is_in_no_frame(self: TestTracebackLocals, answer: Callable[[httpx.Request], httpx.Response]) -> None:
    """Every frame of the raised error, and of its chain, is free of the password."""
    vault = VaultControl(ApiClient(transport=httpx.MockTransport(answer)))

    with pytest.raises(BitwardenError) as exc_info:  # act
      vault.unlock(SecretStr(PASSWORD))

    assert _leaking_frames(exc_info.value) == []

  def test_check_sees_a_plaintext_local(self: TestTracebackLocals) -> None:
    """The walk finds a password held in a local, so a clean result means something."""

    def hold(body: dict[str, Any]) -> None:  # noqa: U100
      raise RuntimeError("held")

    with pytest.raises(RuntimeError) as exc_info:  # act
      hold({"password": SecretStr(PASSWORD).get_secret_value()})

    assert _leaking_frames(exc_info.value) == ["hold:body"]

  @pytest.mark.parametrize("fields", ITEMS, ids=["login", "card"])
  @pytest.mark.parametrize("given", ["template", "fetched"])
  @pytest.mark.parametrize("method", ["add", "modify"])
  def test_item_secrets_are_in_no_frame(self: TestTracebackLocals, method: str, given: str, fields: dict[str, Any]) -> None:
    """A rejected add or modify of a model item leaves its secrets in no frame (#126)."""
    fetched = models.ItemSchema.model_validate(fields | {"object": "item", "id": ITEM_ID})
    item = fetched if given == "fetched" else models.ItemTemplateSchema.model_validate(fields)

    error = _reject_item(method, item)  # act

    assert _leaking_frames(error, tuple(ITEM_SECRETS.values())) == []


def _reject_item(method: str, item: models.ItemSchema | models.ItemTemplateSchema) -> BitwardenError:
  """Send an item to a server that rejects it, and catch the error here.

  Catching it here keeps the calling test's frame, which holds the
  plaintext fixture, off the traceback that is searched.

  Args:
    method: ``add`` or ``modify``.
    item: The item to send.

  Returns:
    The error the rejection raised.

  Raises:
    AssertionError: When nothing was raised.
  """
  items = VaultItems(ApiClient(transport=httpx.MockTransport(_answer_400)))

  try:
    if method == "add":
      items.add(item)

    else:
      items.modify(ITEM_ID, item)

  except BitwardenError as e:
    return e

  raise AssertionError("the rejected item raised nothing")
