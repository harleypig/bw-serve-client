"""Organizations domain class for the Bitwarden Vault Management API.

Mirrors the organization half of the ``Collections & Organizations`` tag in
the API spec. One method per route:

  GET    /object/organization/{id}   - Organizations.get
  GET    /list/object/org-members    - Organizations.list_members
  POST   /confirm/org-member/{id}    - Organizations.confirm_member
  GET    /list/object/organizations  - Organizations.list
"""

from __future__ import annotations

from typing import Any, Optional, Union
from uuid import UUID

from ._generated.models import ConfirmOrgMemberIdPostParameters
from ._generated.models import ListObjectOrganizationsGetParameters
from ._generated.models import ListObjectOrgMembersGetParameters
from ._generated.models import ObjectOrganizationIdGetParameters
from ._generated.models import OrganizationSchema
from ._generated.models import OrgMemberSchema
from .resource import Resource
from .resource import route

OrganizationId = Union[UUID, str]
MemberId = Union[UUID, str]

# The generated confirm model holds the path id and the organizationId
# query in one model, so it validates the path and this model, which holds
# only organizationId, validates the query.
_OrganizationQuery = ListObjectOrgMembersGetParameters


class Organizations(Resource):
  """Operations on the organizations the vault's account belongs to.

  Construction, logging and error handling are :class:`Resource`'s. Every
  method returns what the error handler returned, in place of its result,
  when a failure is handled without raising.
  """

  # ---------------------------------------------------------------------------
  @route("GET", "/object/organization/{id}")
  def get(self: Organizations, organization_id: OrganizationId) -> Union[OrganizationSchema, Any]:
    """Retrieve an Organization you are a member of.

    Read from the local state of the vault, as of its last sync.

    Args:
        organization_id: Unique identifier of the organization.

    Returns:
        The :class:`OrganizationSchema`.
    """
    return self._request(
      "GET",
      "/object/organization/{id}",
      path_params=(ObjectOrganizationIdGetParameters, {
        "id": organization_id
      }),
      response_type=OrganizationSchema,
    )

  # ---------------------------------------------------------------------------
  @route("GET", "/list/object/org-members")
  def list_members(self: Organizations, organization_id: OrganizationId) -> Union[list[OrgMemberSchema], Any]:
    """List members of a specified Organization.

    Args:
        organization_id: Unique identifier of the organization.

    Returns:
        The organization's members, as :class:`OrgMemberSchema`.
    """
    return self._request(
      "GET",
      "/list/object/org-members",
      query=(ListObjectOrgMembersGetParameters, {
        "organizationId": organization_id
      }),
      response_type=list[OrgMemberSchema],
    )

  # ---------------------------------------------------------------------------
  @route("POST", "/confirm/org-member/{id}")
  def confirm_member(self: Organizations, member_id: MemberId, organization_id: OrganizationId) -> Any:
    """Confirm a member to a specified Organization.

    Args:
        member_id: Unique identifier of the member to confirm, as
            ``list_members()`` gives it.
        organization_id: Unique identifier of the organization.

    Returns:
        ``None``, or the error handler's return value.
    """
    return self._request(
      "POST",
      "/confirm/org-member/{id}",
      path_params=(ConfirmOrgMemberIdPostParameters, {
        "id": member_id,
        "organizationId": organization_id
      }),
      query=(_OrganizationQuery, {
        "organizationId": organization_id
      }),
    )

  # ---------------------------------------------------------------------------
  @route("GET", "/list/object/organizations")
  def list(self: Organizations, search: Optional[str] = None) -> Union[list[OrganizationSchema], Any]:
    """List Organizations of which you are a member.

    Args:
        search: List only organizations whose names contain this term.
            When ``None`` or empty, all are returned.

    Returns:
        The matching organizations, as :class:`OrganizationSchema`
        (empty if none match).
    """
    query = (ListObjectOrganizationsGetParameters, {"search": search or None})

    return self._request("GET", "/list/object/organizations", query=query, response_type=list[OrganizationSchema])
