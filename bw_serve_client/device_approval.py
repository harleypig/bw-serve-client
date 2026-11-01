"""DeviceApproval domain class for the Bitwarden Vault Management API.

Mirrors the ``Trusted Device Approval`` tag in the API spec. One
``DeviceApproval`` method per route:

  POST /device-approval/{organizationId}/approve/{request-id} - approve
  POST /device-approval/{organizationId}/approve-all          - approve_all
  POST /device-approval/{organizationId}/deny/{request-id}    - deny
  POST /device-approval/{organizationId}/deny-all             - deny_all
  GET  /device-approval/{organizationId}                      - list
"""

from __future__ import annotations

from typing import Any, Union
from uuid import UUID

from ._generated.models import DeviceApprovalOrganizationIdApproveAllPostParameters
from ._generated.models import DeviceApprovalOrganizationIdApproveRequestIdPostParameters
from ._generated.models import DeviceApprovalOrganizationIdDenyAllPostParameters
from ._generated.models import DeviceApprovalOrganizationIdDenyRequestIdPostParameters
from ._generated.models import DeviceApprovalOrganizationIdGetParameters
from ._generated.models import DeviceApprovalPropertiesSchema
from .resource import Resource
from .resource import route

OrganizationId = Union[UUID, str]
RequestId = Union[UUID, str]


class DeviceApproval(Resource):
  """Approve or deny the trusted-device requests of an organization.

  **Commercial build only.** These routes are registered by the licensed
  Bitwarden CLI build alone; the open-source ``bw`` has none of them, so
  its ``bw serve`` answers every call here with a 404, which arrives as a
  :class:`~bw_serve_client.errors.ValidationError` with ``status_code``
  404. The account also needs permission to manage the organization's
  users' passwords.

  Construction, logging and error handling are :class:`Resource`'s. Every
  method returns what the error handler returned, in place of its result,
  when a failure is handled without raising.
  """

  # ---------------------------------------------------------------------------
  @route("POST", "/device-approval/{organizationId}/approve/{request-id}")
  def approve(self: DeviceApproval, organization_id: OrganizationId, request_id: RequestId) -> Any:
    """Approve a specific device approval request.

    Request identifiers can be retrieved using
    ``GET /device-approval/{organizationId}``. That route is ``list()``.

    Args:
        organization_id: Unique identifier of the organization.
        request_id: Unique identifier of the pending request.

    Returns:
        ``None``, or the error handler's return value.
    """
    return self._request(
      "POST",
      "/device-approval/{organizationId}/approve/{request-id}",
      path_params=(
        DeviceApprovalOrganizationIdApproveRequestIdPostParameters, {
          "organizationId": organization_id,
          "request-id": request_id
        }
      ),
    )

  # ---------------------------------------------------------------------------
  @route("POST", "/device-approval/{organizationId}/approve-all")
  def approve_all(self: DeviceApproval, organization_id: OrganizationId) -> Any:
    """Approve all pending device approval requests.

    Args:
        organization_id: Unique identifier of the organization.

    Returns:
        ``None``, or the error handler's return value.
    """
    return self._request(
      "POST",
      "/device-approval/{organizationId}/approve-all",
      path_params=(DeviceApprovalOrganizationIdApproveAllPostParameters, {
        "organizationId": organization_id
      }),
    )

  # ---------------------------------------------------------------------------
  @route("POST", "/device-approval/{organizationId}/deny/{request-id}")
  def deny(self: DeviceApproval, organization_id: OrganizationId, request_id: RequestId) -> Any:
    """Deny a specific device approval request.

    Request identifiers can be retrieved using
    ``GET /device-approval/{organizationId}``. That route is ``list()``.

    Args:
        organization_id: Unique identifier of the organization.
        request_id: Unique identifier of the pending request.

    Returns:
        ``None``, or the error handler's return value.
    """
    return self._request(
      "POST",
      "/device-approval/{organizationId}/deny/{request-id}",
      path_params=(
        DeviceApprovalOrganizationIdDenyRequestIdPostParameters, {
          "organizationId": organization_id,
          "request-id": request_id
        }
      ),
    )

  # ---------------------------------------------------------------------------
  @route("POST", "/device-approval/{organizationId}/deny-all")
  def deny_all(self: DeviceApproval, organization_id: OrganizationId) -> Any:
    """Deny all pending device approval requests.

    Args:
        organization_id: Unique identifier of the organization.

    Returns:
        ``None``, or the error handler's return value.
    """
    return self._request(
      "POST",
      "/device-approval/{organizationId}/deny-all",
      path_params=(DeviceApprovalOrganizationIdDenyAllPostParameters, {
        "organizationId": organization_id
      }),
    )

  # ---------------------------------------------------------------------------
  @route("GET", "/device-approval/{organizationId}")
  def list(self: DeviceApproval, organization_id: OrganizationId) -> Union[list[DeviceApprovalPropertiesSchema], Any]:
    """Retrieve a list of pending device approval requests.

    Args:
        organization_id: Unique identifier of the organization.

    Returns:
        The pending requests, as :class:`DeviceApprovalPropertiesSchema`
        (empty if there are none). Each carries the requesting device's
        ``fingerprint_phrase``, to compare with the user's before
        approving.
    """
    return self._request(
      "GET",
      "/device-approval/{organizationId}",
      path_params=(DeviceApprovalOrganizationIdGetParameters, {
        "organizationId": organization_id
      }),
      response_type=list[DeviceApprovalPropertiesSchema],
    )
