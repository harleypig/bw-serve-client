"""Tests for the VaultControl domain class."""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, TYPE_CHECKING

from conftest import load_recorded
from pydantic import SecretStr
import pytest
from test_secrets import _assert_clean
from test_secrets import _exposed
from test_secrets import _unlocked
from test_secrets import PASSWORD
from test_secrets import SESSION

from bw_serve_client._generated.models import LockUnlockDataSchema
from bw_serve_client._generated.models import SyncMessageSchema
from bw_serve_client._generated.models import TemplateSchema
from bw_serve_client._generated.models import TemplateStatusSchema
from bw_serve_client.errors import BitwardenError
from bw_serve_client.errors import ExternalServiceError
from bw_serve_client.errors import UserError
from bw_serve_client.errors import ValidationError
from bw_serve_client.vault_control import VaultControl

if TYPE_CHECKING:
  from conftest import MakeClient
  from conftest import ReturningHandler
  import httpx


def _recorded_client(make_client: MakeClient, name: str, **kwargs: Any) -> Any:
  """Build a client that answers with one recorded response.

  Args:
    make_client: The shared client factory.
    name: The recording's case name.
    kwargs: Passed on to the client.

  Returns:
    The client.
  """
  response = load_recorded(name)["response"]
  return make_client(response["status"], json_body=response["body"], **kwargs)


#: One method called with valid arguments.
Call = Callable[[VaultControl], Any]

#: Every method, called with valid arguments, and a recording of its success.
CALLS: dict[str, tuple[Call, str]] = {
  "lock": (lambda vault: vault.lock(), "lock"),
  "unlock": (lambda vault: vault.unlock(PASSWORD), "unlock"),
  "sync": (lambda vault: vault.sync(), "sync"),
  "status": (lambda vault: vault.status(), "status-unlocked"),
}


# -----------------------------------------------------------------------------
class TestLock:
  """Tests for VaultControl.lock."""

  def test_posts_to_lock_and_returns_the_message(self: TestLock, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """POST /lock with no body; the recorded confirmation comes back parsed."""
    vault = VaultControl(_recorded_client(make_client, "lock"))

    result = vault.lock()  # act

    [request] = sent
    assert (request.method, request.url.path, request.content) == ("POST", "/lock", b"")
    assert isinstance(result, LockUnlockDataSchema)
    assert result.title == "Your vault is locked."


# -----------------------------------------------------------------------------
class TestUnlock:
  """Tests for VaultControl.unlock."""

  def test_posts_password_and_returns_session_key(self: TestUnlock, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """The password is sent in the clear; the session key comes back masked."""
    vault = VaultControl(make_client(json_body=_unlocked()))

    result = vault.unlock(PASSWORD)  # act

    [request] = sent
    assert (request.method, request.url.path) == ("POST", "/unlock")
    assert json.loads(request.content) == {"password": PASSWORD}
    assert isinstance(result, SecretStr)
    assert result.get_secret_value() == SESSION

  def test_accepts_a_secret_password(self: TestUnlock, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A SecretStr password is sent as its value."""
    vault = VaultControl(make_client(json_body=_unlocked()))

    vault.unlock(SecretStr(PASSWORD))  # act

    [request] = sent
    assert json.loads(request.content) == {"password": PASSWORD}

  def test_parses_the_recorded_unlock(self: TestUnlock, make_client: MakeClient) -> None:
    """The recorded success yields its (redacted) session key."""
    vault = VaultControl(_recorded_client(make_client, "unlock"))

    result = vault.unlock(PASSWORD)  # act

    assert isinstance(result, SecretStr)
    assert result.get_secret_value() == "<redacted>"

  def test_wrong_password_is_a_user_error(self: TestUnlock, make_client: MakeClient) -> None:
    """The recorded 400 for a wrong password raises a UserError."""
    vault = VaultControl(_recorded_client(make_client, "unlock-wrong-password"))

    with pytest.raises(UserError, match="decryption operation failed") as exc_info:
      vault.unlock("wrong-password")

    assert exc_info.value.status_code == 400

  def test_password_that_is_not_a_string_is_refused(self: TestUnlock, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A password that is not a string fails validation before sending."""
    vault = VaultControl(make_client(json_body=_unlocked()))

    with pytest.raises(ValidationError, match="invalid body"):
      vault.unlock(1234)  # type: ignore[arg-type]

    assert sent == []

  def test_success_without_session_key_fails(self: TestUnlock, make_client: MakeClient) -> None:
    """A success body with no session key is an ExternalServiceError."""
    body = _unlocked()
    del body["data"]["raw"]
    vault = VaultControl(make_client(json_body=body))

    with pytest.raises(ExternalServiceError, match="no session key"):
      vault.unlock(PASSWORD)

  def test_missing_session_key_goes_to_the_handler(
    self: TestUnlock, make_client: MakeClient, returning_handler: ReturningHandler
  ) -> None:
    """With a returning handler, a missing session key returns its value."""
    body = _unlocked()
    del body["data"]["raw"]
    vault = VaultControl(make_client(json_body=body), error_handler=returning_handler)

    result = vault.unlock(PASSWORD)  # act

    assert result is returning_handler.result
    [(category, _message, _status, _cause)] = returning_handler.calls
    assert category is ExternalServiceError


# -----------------------------------------------------------------------------
class TestUnlockKeepsSecrets:
  """Neither the password nor the session key leaks through unlock (#30)."""

  def test_success_shows_neither_secret(
    self: TestUnlockKeepsSecrets, make_client: MakeClient, caplog: pytest.LogCaptureFixture
  ) -> None:
    """Logs at DEBUG and the returned key's str and repr hold no secret."""
    vault = VaultControl(make_client(json_body=_unlocked()))

    with caplog.at_level(logging.DEBUG):  # act
      session = vault.unlock(PASSWORD)

    assert caplog.records
    _assert_clean(_exposed(caplog.records, None, session))

  @pytest.mark.parametrize(
    ("status", "body"),
    [
      (400, {
        "success": False,
        "message": "Invalid master password."
      }),
      (500, {
        "success": False,
        "message": "Internal Server Error"
      }),
      (200, {
        "success": True,
        "data": SESSION
      }),
      (200, {
        "success": True,
        "data": {
          "object": "message",
          "title": "Your vault is now unlocked!"
        }
      }),
    ],
    ids=["rejected", "server-error", "unparseable", "no-session-key"],
  )
  def test_failure_shows_neither_secret(
    self: TestUnlockKeepsSecrets, status: int, body: dict[str, Any], make_client: MakeClient, caplog: pytest.LogCaptureFixture
  ) -> None:
    """A failed unlock's error and logs hold neither secret."""
    vault = VaultControl(make_client(status=status, json_body=body))

    with caplog.at_level(logging.DEBUG), pytest.raises(BitwardenError) as exc_info:
      vault.unlock(PASSWORD)

    _assert_clean(_exposed(caplog.records, exc_info.value))


# -----------------------------------------------------------------------------
class TestSync:
  """Tests for VaultControl.sync."""

  def test_posts_to_sync_without_force(self: TestSync, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """POST /sync with no query; the recorded confirmation comes back parsed."""
    vault = VaultControl(_recorded_client(make_client, "sync"))

    result = vault.sync()  # act

    [request] = sent
    assert (request.method, request.url.path, request.url.query) == ("POST", "/sync", b"")
    assert isinstance(result, SyncMessageSchema)
    assert result.title == "Syncing complete."

  @pytest.mark.parametrize(("force", "query"), [(True, b"force=true"), (False, b"force=false")])
  def test_sends_force(self: TestSync, force: bool, query: bytes, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """Force is sent as a query parameter in bw serve's spelling."""
    vault = VaultControl(_recorded_client(make_client, "sync"))

    vault.sync(force=force)  # act

    [request] = sent
    assert request.url.query == query

  def test_refuses_a_force_that_is_not_a_boolean(self: TestSync, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A force that is not a boolean fails validation before sending."""
    vault = VaultControl(make_client())

    with pytest.raises(ValidationError, match="invalid query"):
      vault.sync(force="sometimes")  # type: ignore[arg-type]

    assert sent == []


# -----------------------------------------------------------------------------
class TestStatus:
  """Tests for VaultControl.status."""

  @pytest.mark.parametrize(("name", "state"), [("status-locked", "locked"), ("status-unlocked", "unlocked")])
  def test_returns_the_recorded_status(
    self: TestStatus, name: str, state: str, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """GET /status returns the template with the vault's recorded state."""
    vault = VaultControl(_recorded_client(make_client, name))

    result = vault.status()  # act

    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/status")
    assert isinstance(result, TemplateSchema)
    assert result.status is TemplateStatusSchema(state)
    assert result.user_email == "fixture-recorder@example.com"


# -----------------------------------------------------------------------------
class TestContract:
  """The parts of the API class contract every method shares."""

  @pytest.mark.parametrize("name", list(CALLS))
  def test_sends_no_authorization_header(self: TestContract, name: str, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """Bw serve has no endpoint auth, so no Authorization header is sent."""
    call, recording = CALLS[name]
    vault = VaultControl(_recorded_client(make_client, recording))

    call(vault)  # act

    [request] = sent
    assert "authorization" not in request.headers

  @pytest.mark.parametrize("name", list(CALLS))
  def test_server_error_raises_external_service_error(self: TestContract, name: str, make_client: MakeClient) -> None:
    """A 5xx is an ExternalServiceError carrying the status."""
    vault = VaultControl(make_client(status=500, text_body="Internal Server Error"))

    with pytest.raises(ExternalServiceError) as exc_info:
      CALLS[name][0](vault)

    assert exc_info.value.status_code == 500

  @pytest.mark.parametrize("name", list(CALLS))
  def test_handled_failure_returns_the_handlers_value(
    self: TestContract, name: str, make_client: MakeClient, returning_handler: ReturningHandler
  ) -> None:
    """A handler that returns instead of raising supplies the method's result."""
    client = make_client(status=400, json_body={"success": False, "message": "You are not logged in."})
    vault = VaultControl(client, error_handler=returning_handler)

    result = CALLS[name][0](vault)  # act

    assert result is returning_handler.result
    [(category, _message, status_code, _cause)] = returning_handler.calls
    assert (category, status_code) == (UserError, 400)
