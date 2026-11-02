"""Tests for the Utilities domain class."""

from __future__ import annotations

import logging
from typing import Any, Callable, TYPE_CHECKING
from urllib.parse import parse_qsl
from urllib.parse import urlsplit

from conftest import load_recorded
from pydantic import SecretStr
import pytest

from bw_serve_client.errors import ExternalServiceError
from bw_serve_client.errors import ValidationError
from bw_serve_client.utilities import Utilities

if TYPE_CHECKING:
  from conftest import MakeClient
  from conftest import ReturningHandler
  import httpx

# Made-up, distinctive enough that a partial match cannot be chance.
GENERATED = "made-up-generated-pw-K3v8"


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


def _generated(value: str = GENERATED) -> dict[str, Any]:
  """Build bw serve's success body for /generate.

  Args:
    value: The generated password.

  Returns:
    The response body.
  """
  return {"success": True, "data": {"object": "string", "data": value}}


def _recorded_query(name: str) -> dict[str, str]:
  """Read the query a recording sent.

  Args:
    name: The recording's case name.

  Returns:
    The query parameters, by name.
  """
  return dict(parse_qsl(urlsplit(load_recorded(name)["request"]["path"]).query))


#: One method called with valid arguments.
Call = Callable[[Utilities], Any]

#: Every method, called with valid arguments, and a recording of its success.
CALLS: dict[str, tuple[Call, str]] = {
  "template": (lambda utilities: utilities.template("folder"), "template-folder"),
  "fingerprint": (lambda utilities: utilities.fingerprint(), "fingerprint"),
  "generate": (lambda utilities: utilities.generate(), "generate"),
}


# -----------------------------------------------------------------------------
class TestTemplate:
  """Tests for Utilities.template."""

  @pytest.mark.parametrize(
    ("object_type", "name"),
    [
      ("folder", "template-folder"),
      ("item", "template-item"),
      ("item.login", "template-item-login"),
      ("org-collection", "template-org-collection"),
      ("item-collections", "template-item-collections"),
    ],
  )
  def test_returns_the_recorded_template(
    self: TestTemplate, object_type: str, name: str, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """GET /object/template/{type} returns the template itself."""
    payload = load_recorded(name)
    utilities = Utilities(_recorded_client(make_client, name))

    result = utilities.template(object_type)  # act

    [request] = sent
    assert (request.method, request.url.path) == ("GET", payload["request"]["path"])
    assert result == payload["response"]["body"]["data"]["template"]

  def test_item_collections_template_is_a_list(self: TestTemplate, make_client: MakeClient) -> None:
    """The item-collections template is a list of ids, not an object."""
    utilities = Utilities(_recorded_client(make_client, "template-item-collections"))

    result = utilities.template("item-collections")  # act

    assert result == ["collection-id1", "collection-id2"]

  def test_refuses_an_unknown_type(self: TestTemplate, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A type the spec does not list fails validation before sending."""
    utilities = Utilities(make_client())

    with pytest.raises(ValidationError, match="invalid path"):
      utilities.template("send")

    assert sent == []


# -----------------------------------------------------------------------------
class TestFingerprint:
  """Tests for Utilities.fingerprint."""

  def test_returns_the_recorded_phrase(self: TestFingerprint, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """GET /object/fingerprint/me returns the phrase as a plain string."""
    utilities = Utilities(_recorded_client(make_client, "fingerprint"))

    result = utilities.fingerprint()  # act

    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/object/fingerprint/me")
    assert result == "perjury-manor-both-deputy-shaking"


# -----------------------------------------------------------------------------
class TestGenerate:
  """Tests for Utilities.generate."""

  def test_defaults_send_no_query(self: TestGenerate, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """With no arguments, GET /generate carries no query parameters."""
    utilities = Utilities(make_client(json_body=_generated()))

    utilities.generate()  # act

    [request] = sent
    assert (request.method, request.url.path, request.url.query) == ("GET", "/generate", b"")

  def test_returns_the_password_masked(self: TestGenerate, make_client: MakeClient) -> None:
    """The generated password is a SecretStr whose repr hides it."""
    utilities = Utilities(make_client(json_body=_generated()))

    result = utilities.generate()  # act

    assert isinstance(result, SecretStr)
    assert result.get_secret_value() == GENERATED
    assert GENERATED not in repr(result) + str(result)

  def test_password_stays_out_of_logs(self: TestGenerate, make_client: MakeClient, caplog: pytest.LogCaptureFixture) -> None:
    """Nothing logged at DEBUG holds the generated password."""
    utilities = Utilities(make_client(json_body=_generated()))

    with caplog.at_level(logging.DEBUG):  # act
      utilities.generate()

    assert caplog.records
    assert all(GENERATED not in record.getMessage() for record in caplog.records)

  def test_password_options_match_the_recording(self: TestGenerate, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """The minimum and avoid-ambiguous options send the recorded query."""
    utilities = Utilities(_recorded_client(make_client, "generate-minimums"))

    result = utilities.generate(
      length=24, uppercase=True, lowercase=True, number=True, special=True, min_number=3, min_special=3, avoid_ambiguous=True
    )  # act

    [request] = sent
    assert dict(request.url.params) == _recorded_query("generate-minimums")
    assert isinstance(result, SecretStr)

  def test_passphrase_options_match_the_recording(self: TestGenerate, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """The passphrase options send the recorded query."""
    utilities = Utilities(_recorded_client(make_client, "generate-passphrase"))

    utilities.generate(passphrase=True, words=4, separator="-", capitalize=True, include_number=True)  # act

    [request] = sent
    assert dict(request.url.params) == _recorded_query("generate-passphrase")

  # bw serve's generator reads ambiguous=true as "avoid ambiguous
  # characters" (it passes !ambiguous to a generator whose own flag means
  # "may include"), so avoid_ambiguous must map straight onto it.
  @pytest.mark.parametrize(("avoid", "sent_value"), [(True, "true"), (False, "false")])
  def test_avoid_ambiguous_is_sent_as_ambiguous(
    self: TestGenerate, avoid: bool, sent_value: str, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """Avoid_ambiguous=True sends ambiguous=true, and False sends false."""
    utilities = Utilities(make_client(json_body=_generated()))

    utilities.generate(avoid_ambiguous=avoid)  # act

    [request] = sent
    assert dict(request.url.params) == {"ambiguous": sent_value}

  def test_refuses_a_length_that_is_not_a_number(self: TestGenerate, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A length that is not an integer fails validation before sending."""
    utilities = Utilities(make_client(json_body=_generated()))

    with pytest.raises(ValidationError, match="invalid query"):
      utilities.generate(length="long")  # type: ignore[arg-type]

    assert sent == []

  def test_options_are_keyword_only(self: TestGenerate, make_client: MakeClient) -> None:
    """Thirteen options of a few types are too easy to pass in the wrong slot."""
    utilities = Utilities(make_client(json_body=_generated()))

    with pytest.raises(TypeError):
      utilities.generate(24)  # type: ignore[misc]


# -----------------------------------------------------------------------------
class TestContract:
  """The parts of the API class contract every method shares."""

  @pytest.mark.parametrize("name", list(CALLS))
  def test_sends_no_authorization_header(self: TestContract, name: str, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """Bw serve has no endpoint auth, so no Authorization header is sent."""
    call, recording = CALLS[name]
    utilities = Utilities(_recorded_client(make_client, recording))

    call(utilities)  # act

    [request] = sent
    assert "authorization" not in request.headers

  @pytest.mark.parametrize("name", list(CALLS))
  def test_server_error_raises_external_service_error(self: TestContract, name: str, make_client: MakeClient) -> None:
    """A 5xx is an ExternalServiceError carrying the status."""
    utilities = Utilities(make_client(status=500, text_body="Internal Server Error"))

    with pytest.raises(ExternalServiceError) as exc_info:
      CALLS[name][0](utilities)

    assert exc_info.value.status_code == 500

  @pytest.mark.parametrize("name", list(CALLS))
  def test_handled_failure_returns_the_handlers_value(
    self: TestContract, name: str, make_client: MakeClient, returning_handler: ReturningHandler
  ) -> None:
    """A handler that returns instead of raising supplies the method's result."""
    client = make_client(status=400, json_body={"success": False, "message": "Bad request."})
    utilities = Utilities(client, error_handler=returning_handler)

    result = CALLS[name][0](utilities)  # act

    assert result is returning_handler.result
    [(category, message, status_code, _cause)] = returning_handler.calls
    assert (category, message, status_code) == (ValidationError, "Bad request.", 400)

  @pytest.mark.parametrize("name", list(CALLS))
  def test_unparseable_success_goes_to_the_handler(
    self: TestContract, name: str, make_client: MakeClient, returning_handler: ReturningHandler
  ) -> None:
    """A success whose data does not parse reaches the handler, not the caller."""
    client = make_client(json_body={"success": True, "data": {"object": "list"}})
    utilities = Utilities(client, error_handler=returning_handler)

    result = CALLS[name][0](utilities)  # act

    assert result is returning_handler.result
    [(category, _message, _status, _cause)] = returning_handler.calls
    assert category is ExternalServiceError
