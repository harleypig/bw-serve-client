"""Tests for the Organizations domain class."""

from __future__ import annotations

from collections.abc import Callable
import logging
from typing import Any, TYPE_CHECKING
from uuid import UUID

from conftest import load_recorded
import pytest

from bw_serve_client._generated.models import OrganizationSchema
from bw_serve_client._generated.models import OrgMemberSchema
from bw_serve_client.errors import ExternalServiceError
from bw_serve_client.errors import ValidationError
from bw_serve_client.organizations import Organizations

if TYPE_CHECKING:
  from conftest import MakeClient
  from conftest import ReturningHandler
  import httpx

# The recorder's organization, and a member id it does not have.
ORG_ID = "f64481e2-dc5d-48cf-8db1-e6d5331fe910"
UNKNOWN_ID = "7d3c0d52-31a6-4c47-9b0e-0b1d1c5c0a11"

#: Calls one method with valid arguments.
Call = Callable[[Organizations], Any]

CALLS: dict[str, Call] = {
  "get": lambda orgs: orgs.get(ORG_ID),
  "list_members": lambda orgs: orgs.list_members(ORG_ID),
  "confirm_member": lambda orgs: orgs.confirm_member(UNKNOWN_ID, ORG_ID),
  "list": lambda orgs: orgs.list(),
}

#: Calls one method with an organization id that is not a UUID.
BAD_ORG_CALLS: dict[str, Call] = {
  "get": lambda orgs: orgs.get("not-a-uuid"),
  "list_members": lambda orgs: orgs.list_members("not-a-uuid"),
  "confirm_member": lambda orgs: orgs.confirm_member(UNKNOWN_ID, "not-a-uuid"),
}


def _recorded(case: str) -> Any:
  """Return the response body of one recording.

  Args:
    case: The recording's name.

  Returns:
    The body bw serve sent.
  """
  return load_recorded(case)["response"]["body"]


# -----------------------------------------------------------------------------
class TestOrganizationsGet:
  """Tests for Organizations.get."""

  def test_gets_and_parses_the_recorded_organization(
    self: TestOrganizationsGet, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """GET /object/organization/{id} parses into OrganizationSchema."""
    orgs = Organizations(make_client(json_body=_recorded("organization-get")))

    result = orgs.get(UUID(ORG_ID))  # act

    [request] = sent
    assert (request.method, request.url.path) == ("GET", f"/object/organization/{ORG_ID}")
    assert isinstance(result, OrganizationSchema)
    assert (result.id, result.name, result.enabled) == (UUID(ORG_ID), "Recorded organization", True)


# -----------------------------------------------------------------------------
class TestOrganizationsListMembers:
  """Tests for Organizations.list_members."""

  def test_lists_and_parses_the_recorded_members(
    self: TestOrganizationsListMembers, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """The organization id is the organizationId query parameter."""
    orgs = Organizations(make_client(json_body=_recorded("org-members-list")))

    result = orgs.list_members(ORG_ID)  # act

    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/list/object/org-members")
    assert dict(request.url.params) == {"organizationId": ORG_ID}
    [member] = result
    assert isinstance(member, OrgMemberSchema)
    assert (member.email, member.status, member.two_factor_enabled) == ("fixture-recorder@example.com", 2, False)

  def test_recorded_unknown_organization_raises_validation_error(
    self: TestOrganizationsListMembers, make_client: MakeClient
  ) -> None:
    """Bw serve's 400 for an organization the account is not in."""
    recorded = load_recorded("org-members-list-unknown-org")["response"]
    orgs = Organizations(make_client(status=recorded["status"], json_body=recorded["body"]))

    with pytest.raises(ValidationError, match="Organization not found.") as exc_info:
      orgs.list_members(UNKNOWN_ID)

    assert exc_info.value.status_code == 400


# -----------------------------------------------------------------------------
class TestOrganizationsConfirmMember:
  """Tests for Organizations.confirm_member."""

  def test_posts_member_in_path_and_organization_in_query(
    self: TestOrganizationsConfirmMember, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """POST /confirm/org-member/{id}?organizationId=..., no body, returns None."""
    orgs = Organizations(make_client(json_body={"success": True}))

    result = orgs.confirm_member(UNKNOWN_ID, ORG_ID)  # act

    [request] = sent
    assert result is None
    assert (request.method, request.url.path) == ("POST", f"/confirm/org-member/{UNKNOWN_ID}")
    assert dict(request.url.params) == {"organizationId": ORG_ID}
    assert request.content == b""

  def test_rejects_non_uuid_member_id(
    self: TestOrganizationsConfirmMember, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """A member id that is not a UUID is refused before sending."""
    orgs = Organizations(make_client())

    with pytest.raises(ValidationError, match="invalid path"):
      orgs.confirm_member("not-a-uuid", ORG_ID)

    assert sent == []

  def test_recorded_unknown_member_raises_validation_error(self: TestOrganizationsConfirmMember, make_client: MakeClient) -> None:
    """Bw serve's 400 for a user the organization does not have."""
    recorded = load_recorded("org-member-confirm-unknown")["response"]
    orgs = Organizations(make_client(status=recorded["status"], json_body=recorded["body"]))

    with pytest.raises(ValidationError, match="isn't a member of the organization"):
      orgs.confirm_member(UNKNOWN_ID, ORG_ID)


# -----------------------------------------------------------------------------
class TestOrganizationsList:
  """Tests for Organizations.list."""

  def test_lists_and_parses_the_recorded_organizations(
    self: TestOrganizationsList, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """GET /list/object/organizations with no query parses every entry."""
    orgs = Organizations(make_client(json_body=_recorded("organizations-list")))

    result = orgs.list()  # act

    [request] = sent
    assert (request.method, request.url.path, request.url.query) == ("GET", "/list/object/organizations", b"")
    assert [(o.id, o.name) for o in result] == [(UUID(ORG_ID), "Recorded organization")]

  def test_search_is_a_query_parameter(self: TestOrganizationsList, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A search term is forwarded as the search query parameter."""
    orgs = Organizations(make_client(json_body={"success": True, "data": {"object": "list", "data": []}}))

    result = orgs.list(search="Recorded")  # act

    [request] = sent
    assert dict(request.url.params) == {"search": "Recorded"}
    assert result == []

  def test_empty_search_sends_no_query(self: TestOrganizationsList, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """An empty search string is treated as no filter."""
    orgs = Organizations(make_client(json_body={"success": True, "data": {"object": "list", "data": []}}))

    orgs.list(search="")  # act

    [request] = sent
    assert request.url.query == b""


# -----------------------------------------------------------------------------
class TestOrganizationsContract:
  """The parts of the API class contract every Organizations method shares."""

  @pytest.mark.parametrize("call", BAD_ORG_CALLS.values(), ids=BAD_ORG_CALLS.keys())
  def test_rejects_non_uuid_organization_id(
    self: TestOrganizationsContract, call: Call, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """An organization id that is not a UUID is refused before sending."""
    orgs = Organizations(make_client())

    with pytest.raises(ValidationError, match="invalid"):
      call(orgs)

    assert sent == []

  @pytest.mark.parametrize("call", CALLS.values(), ids=CALLS.keys())
  def test_sends_no_authorization_header(
    self: TestOrganizationsContract, call: Call, make_client: MakeClient, sent: list[httpx.Request],
    returning_handler: ReturningHandler
  ) -> None:
    """Bw serve has no endpoint auth, so no Authorization header is sent."""
    # The reply is beside the point; the handler absorbs a reply that does
    # not parse, so one body serves every method.
    orgs = Organizations(make_client(json_body={"success": True}), error_handler=returning_handler)

    call(orgs)  # act

    [request] = sent
    assert "authorization" not in request.headers

  @pytest.mark.parametrize("call", CALLS.values(), ids=CALLS.keys())
  def test_server_error_raises_external_service_error(self: TestOrganizationsContract, call: Call, make_client: MakeClient) -> None:
    """A 5xx is an ExternalServiceError carrying the status."""
    orgs = Organizations(make_client(status=500, text_body="Internal Server Error"))

    with pytest.raises(ExternalServiceError) as exc_info:
      call(orgs)

    assert exc_info.value.status_code == 500

  @pytest.mark.parametrize("call", CALLS.values(), ids=CALLS.keys())
  def test_handled_failure_returns_the_handlers_value(
    self: TestOrganizationsContract, call: Call, make_client: MakeClient, returning_handler: ReturningHandler
  ) -> None:
    """A handler that returns instead of raising supplies the method's result."""
    client = make_client(status=400, json_body={"success": False, "message": "Not found."})
    orgs = Organizations(client, error_handler=returning_handler)

    result = call(orgs)  # act

    assert result is returning_handler.result
    [(category, message, status_code, _cause)] = returning_handler.calls
    assert (category, message, status_code) == (ValidationError, "Not found.", 400)

  def test_response_that_does_not_match_is_an_external_service_error(
    self: TestOrganizationsContract, make_client: MakeClient
  ) -> None:
    """A 2xx whose data is not an organization is bw serve's fault."""
    orgs = Organizations(make_client(json_body={"success": True, "data": {"id": "not-a-uuid"}}))

    with pytest.raises(ExternalServiceError, match="does not match"):
      orgs.get(ORG_ID)


# -----------------------------------------------------------------------------
class TestOrganizationsInit:
  """Tests for Organizations construction and DI hooks."""

  def test_uses_provided_logger(self: TestOrganizationsInit, make_client: MakeClient, caplog: pytest.LogCaptureFixture) -> None:
    """Injected logger is used for debug output."""
    orgs = Organizations(make_client(json_body=_recorded("organizations-list")), logger=logging.getLogger("test.organizations"))

    with caplog.at_level(logging.DEBUG, logger="test.organizations"):  # act
      orgs.list()

    assert any(r.name == "test.organizations" for r in caplog.records)

  def test_falls_back_to_client_logger(self: TestOrganizationsInit, make_client: MakeClient) -> None:
    """When no logger is provided, the client's logger is used."""
    client = make_client()

    orgs = Organizations(client)  # act

    assert orgs.logger is client.logger
