"""DeviceApproval domain class for the Bitwarden Vault Management API.

Mirrors the ``Trusted Device Approval`` tag in the API spec. One
``DeviceApproval`` method per route::

  POST /device-approval/{organizationId}/approve/{request-id} - approve
  POST /device-approval/{organizationId}/approve-all          - approve_all
  POST /device-approval/{organizationId}/deny/{request-id}    - deny
  POST /device-approval/{organizationId}/deny-all             - deny_all
  GET  /device-approval/{organizationId}                      - list
"""

from __future__ import annotations

from typing import Any, Union

from ._generated.models import DeviceApprovalOrganizationIdApproveAllPostParameters
from ._generated.models import DeviceApprovalOrganizationIdApproveRequestIdPostParameters
from ._generated.models import DeviceApprovalOrganizationIdDenyAllPostParameters
from ._generated.models import DeviceApprovalOrganizationIdDenyRequestIdPostParameters
from ._generated.models import DeviceApprovalOrganizationIdGetParameters
from ._generated.models import DeviceApprovalPropertiesSchema
from .resource import ObjectId
from .resource import Resource
from .resource import route

OrganizationId = ObjectId
RequestId = ObjectId


class DeviceApproval(Resource):
  """Approve or deny the trusted-device requests of an organization.

  **Needs the routes in the CLI and the endpoint on the server.** The npm
  ``@bitwarden/cli`` 2026.10.1 build includes these routes. A CLI build
  without them makes ``bw serve`` answer every call here with a 404, a
  :class:`~bw_serve_client.errors.ValidationError` with ``status_code``
  404. With the routes, a server that lacks the endpoint (Vaultwarden
  1.37.4) answers through ``bw serve`` as a 400, a ``ValidationError``
  with ``status_code`` 400 whose message carries the server's 404. The
  account also needs permission to manage the organization's users'
  passwords.

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
