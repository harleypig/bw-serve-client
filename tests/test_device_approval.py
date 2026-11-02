"""Tests for the DeviceApproval domain class.

There is no recording: the routes exist only in the licensed CLI build,
and the recorder runs the open-source one. Replies come from the patched
spec's own examples instead.
"""

from __future__ import annotations

from collections.abc import Callable
import json
import logging
from pathlib import Path
from typing import Any, TYPE_CHECKING
from uuid import UUID

from conftest import load_recorded
import pytest

from bw_serve_client._generated.models import DeviceApprovalPropertiesSchema
from bw_serve_client.device_approval import DeviceApproval
from bw_serve_client.errors import ExternalServiceError
from bw_serve_client.errors import ValidationError

if TYPE_CHECKING:
  from conftest import MakeClient
  from conftest import ReturningHandler
  import httpx

SPEC = json.loads((Path(__file__).resolve().parent.parent / "upstream" / "vault-management-api-fixed.json").read_text())

ORG_ID = "3c89a31d-f1cc-4673-8d5a-ae2700f9860d"
REQUEST_ID = "ba624b21-1c8a-43b3-a713-ae0000eabdec"

#: Calls one method with valid arguments.
Call = Callable[[DeviceApproval], Any]

CALLS: dict[str, Call] = {
  "approve": lambda d: d.approve(ORG_ID, REQUEST_ID),
  "approve_all": lambda d: d.approve_all(ORG_ID),
  "deny": lambda d: d.deny(ORG_ID, REQUEST_ID),
  "deny_all": lambda d: d.deny_all(ORG_ID),
  "list": lambda d: d.list(ORG_ID),
}

#: Calls one method with an organization id that is not a UUID.
BAD_ORG_CALLS: dict[str, Call] = {
  "approve": lambda d: d.approve("not-a-uuid", REQUEST_ID),
  "approve_all": lambda d: d.approve_all("not-a-uuid"),
  "deny": lambda d: d.deny("not-a-uuid", REQUEST_ID),
  "deny_all": lambda d: d.deny_all("not-a-uuid"),
  "list": lambda d: d.list("not-a-uuid"),
}

#: The action routes: method name, and the path it posts to.
ACTIONS: dict[str, tuple[Call, str]] = {
  "approve": (CALLS["approve"], f"/device-approval/{ORG_ID}/approve/{REQUEST_ID}"),
  "approve_all": (CALLS["approve_all"], f"/device-approval/{ORG_ID}/approve-all"),
  "deny": (CALLS["deny"], f"/device-approval/{ORG_ID}/deny/{REQUEST_ID}"),
  "deny_all": (CALLS["deny_all"], f"/device-approval/{ORG_ID}/deny-all"),
}


def _spec_example(method: str, path: str) -> Any:
  """Return the spec's 200 example for one route.

  Args:
    method: The HTTP method, lower case.
    path: The path template, as the spec spells it.

  Returns:
    The example body.
  """
  return SPEC["paths"][path][method]["responses"]["200"]["content"]["application/json"]["example"]


def _list_reply() -> dict[str, Any]:
  """Return the list route's reply: the spec's example, in its list envelope.

  Returns:
    The reply bw serve sends.
  """
  return _spec_example("get", "/device-approval/{organizationId}")


# -----------------------------------------------------------------------------
class TestDeviceApprovalList:
  """Tests for DeviceApproval.list."""

  def test_gets_and_parses_the_spec_example(
    self: TestDeviceApprovalList, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """GET /device-approval/{organizationId} parses each pending request."""
    approvals = DeviceApproval(make_client(json_body=_list_reply()))

    result = approvals.list(UUID(ORG_ID))  # act

    [request] = sent
    assert (request.method, request.url.path, request.url.query) == ("GET", f"/device-approval/{ORG_ID}", b"")
    [pending] = result
    assert isinstance(pending, DeviceApprovalPropertiesSchema)
    assert (pending.id, pending.email, pending.organization_user_id) == (REQUEST_ID, "orguser@bitwarden.com", ORG_ID)
    assert pending.fingerprint_phrase == "alarm-unfold-steering-deftly-pretext"

  def test_bare_array_reply_is_an_external_service_error(self: TestDeviceApprovalList, make_client: MakeClient) -> None:
    """A reply of the requests alone, without the envelope, is not accepted."""
    approvals = DeviceApproval(make_client(json_body=_list_reply()["data"]["data"]))

    with pytest.raises(ExternalServiceError, match="no data member"):
      approvals.list(ORG_ID)

  def test_permission_failure_raises_validation_error(self: TestDeviceApprovalList, make_client: MakeClient) -> None:
    """Bw serve's 400 for an account that cannot manage the organization."""
    message = "You do not have permission to approve pending device authorization requests."
    approvals = DeviceApproval(make_client(status=400, json_body={"success": False, "message": message}))

    with pytest.raises(ValidationError, match="You do not have permission") as exc_info:
      approvals.list(ORG_ID)

    assert exc_info.value.status_code == 400


# -----------------------------------------------------------------------------
class TestDeviceApprovalActions:
  """Tests for approve, approve_all, deny and deny_all."""

  @pytest.mark.parametrize(("call", "path"), ACTIONS.values(), ids=ACTIONS.keys())
  def test_posts_to_the_route_and_returns_none(
    self: TestDeviceApprovalActions, call: Call, path: str, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """Each action posts no body and answers the spec's bare success."""
    approvals = DeviceApproval(make_client(json_body=_spec_example("post", "/device-approval/{organizationId}/approve-all")))

    result = call(approvals)  # act

    [request] = sent
    assert result is None
    assert (request.method, request.url.path, request.url.query, request.content) == ("POST", path, b"", b"")

  @pytest.mark.parametrize(
    "call", [lambda d: d.approve(ORG_ID, "not-a-uuid"), lambda d: d.deny(ORG_ID, "not-a-uuid")], ids=["approve", "deny"]
  )
  def test_rejects_non_uuid_request_id(
    self: TestDeviceApprovalActions, call: Call, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """A request id that is not a UUID is refused before sending."""
    approvals = DeviceApproval(make_client())

    with pytest.raises(ValidationError, match="request-id"):
      call(approvals)

    assert sent == []


# -----------------------------------------------------------------------------
class TestDeviceApprovalContract:
  """The parts of the API class contract every DeviceApproval method shares."""

  @pytest.mark.parametrize("call", BAD_ORG_CALLS.values(), ids=BAD_ORG_CALLS.keys())
  def test_rejects_non_uuid_organization_id(
    self: TestDeviceApprovalContract, call: Call, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """An organization id that is not a UUID is refused before sending."""
    approvals = DeviceApproval(make_client())

    with pytest.raises(ValidationError, match="invalid path"):
      call(approvals)

    assert sent == []

  @pytest.mark.parametrize("call", CALLS.values(), ids=CALLS.keys())
  def test_open_source_build_answers_404(self: TestDeviceApprovalContract, call: Call, make_client: MakeClient) -> None:
    """On the open-source build the route is unknown: a 404 ValidationError."""
    recorded = load_recorded("unknown-route")["response"]
    approvals = DeviceApproval(make_client(status=recorded["status"], text_body=recorded["body"]))

    with pytest.raises(ValidationError) as exc_info:
      call(approvals)

    assert exc_info.value.status_code == 404

  @pytest.mark.parametrize("call", CALLS.values(), ids=CALLS.keys())
  def test_sends_no_authorization_header(
    self: TestDeviceApprovalContract, call: Call, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """Bw serve has no endpoint auth, so no Authorization header is sent."""
    approvals = DeviceApproval(make_client(json_body=_list_reply()))

    call(approvals)  # act

    [request] = sent
    assert "authorization" not in request.headers

  @pytest.mark.parametrize("call", CALLS.values(), ids=CALLS.keys())
  def test_server_error_raises_external_service_error(
    self: TestDeviceApprovalContract, call: Call, make_client: MakeClient
  ) -> None:
    """A 5xx is an ExternalServiceError carrying the status."""
    approvals = DeviceApproval(make_client(status=500, text_body="Internal Server Error"))

    with pytest.raises(ExternalServiceError) as exc_info:
      call(approvals)

    assert exc_info.value.status_code == 500

  @pytest.mark.parametrize("call", CALLS.values(), ids=CALLS.keys())
  def test_handled_failure_returns_the_handlers_value(
    self: TestDeviceApprovalContract, call: Call, make_client: MakeClient, returning_handler: ReturningHandler
  ) -> None:
    """A handler that returns instead of raising supplies the method's result."""
    client = make_client(status=400, json_body={"success": False, "message": "The request id is invalid."})
    approvals = DeviceApproval(client, error_handler=returning_handler)

    result = call(approvals)  # act

    assert result is returning_handler.result
    [(category, message, status_code, _cause)] = returning_handler.calls
    assert (category, message, status_code) == (ValidationError, "The request id is invalid.", 400)


# -----------------------------------------------------------------------------
class TestDeviceApprovalInit:
  """Tests for DeviceApproval construction and DI hooks."""

  def test_uses_provided_logger(self: TestDeviceApprovalInit, make_client: MakeClient, caplog: pytest.LogCaptureFixture) -> None:
    """Injected logger is used for debug output."""
    approvals = DeviceApproval(make_client(json_body=_list_reply()), logger=logging.getLogger("test.device_approval"))

    with caplog.at_level(logging.DEBUG, logger="test.device_approval"):  # act
      approvals.list(ORG_ID)

    assert any(r.name == "test.device_approval" for r in caplog.records)

  def test_falls_back_to_client_logger(self: TestDeviceApprovalInit, make_client: MakeClient) -> None:
    """When no logger is provided, the client's logger is used."""
    client = make_client()

    approvals = DeviceApproval(client)  # act

    assert approvals.logger is client.logger
