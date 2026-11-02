"""Sends domain class for the Bitwarden Vault Management API.

Mirrors the ``Send`` tag in the API spec. One method per route::

  POST   /object/send                - Sends.add
  PUT    /object/send/{id}           - Sends.modify
  GET    /object/send/{id}           - Sends.get
  DELETE /object/send/{id}           - Sends.delete
  GET    /list/object/send           - Sends.list
  POST   /send/{id}/remove-password  - Sends.remove_password

``GET /send/list``, the spec's alias for ``GET /list/object/send``, is not
offered: bw serve answers it with every Send's ``key`` empty and an
``accessUrl`` ending in ``/undefined``, so the Sends it lists cannot be
opened. ``Sends.list`` uses the object route, which returns both.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, TYPE_CHECKING, Union

from pydantic import SecretStr

from ._generated.models import ListObjectSendGetParameters
from ._generated.models import ObjectSendIdDeleteParameters
from ._generated.models import ObjectSendIdGetParameters
from ._generated.models import ObjectSendIdPutParameters
from ._generated.models import SendIdRemovePasswordPostParameters
from ._generated.models import SendSchema
from ._generated.models import SendTemplateSchema
from ._generated.models import SendTypeSchema
from .resource import ObjectId
from .resource import Resource
from .resource import route

if TYPE_CHECKING:
  from collections.abc import Sequence

SendId = ObjectId
Password = Union[SecretStr, str]
Timestamp = Union[datetime, str]


# -----------------------------------------------------------------------------
def _template(
  name: str,
  text: str,
  hidden: bool,
  notes: Optional[str],
  password: Optional[Password],
  deletion_date: Optional[Timestamp],
  expiration_date: Optional[Timestamp],
  max_access_count: Optional[int],
  emails: Optional[Sequence[str]],
  disabled: bool,
  hide_email: Optional[bool],
) -> dict[str, Any]:
  """Build the request body for a text Send, as ``send.template`` names it.

  Returns:
    The body's fields, keyed by the template's field names.
  """
  if isinstance(password, SecretStr):
    password = password.get_secret_value()

  return {
    "name": name,
    "type": SendTypeSchema.INTEGER_0,
    "text": {
      "text": text,
      "hidden": hidden
    },
    "notes": notes,
    "password": password,
    "deletion_date": deletion_date,
    "expiration_date": expiration_date,
    "max_access_count": max_access_count,
    "emails": emails,
    "disabled": disabled,
    "hide_email": hide_email,
  }


class Sends(Resource):
  """Send operations on a Bitwarden vault.

  Only text Sends are offered: the spec documents no other kind through
  bw serve, so ``add`` and ``modify`` always send ``"type": 0``.

  The Send's ``key``, ``password`` and ``accessUrl`` -- the access URL
  carries the key -- come back as ``SecretStr``, so they stay out of reprs
  and logs; read them with ``get_secret_value()``.

  Construction, logging and error handling are :class:`Resource`'s. Every
  method returns what the error handler returned, in place of its result,
  when a failure is handled without raising.
  """

  # ---------------------------------------------------------------------------
  @route("POST", "/object/send")
  def add(
    self: Sends,
    name: str,
    text: str,
    *,
    hidden: bool = False,
    notes: Optional[str] = None,
    password: Optional[Password] = None,
    deletion_date: Optional[Timestamp] = None,
    expiration_date: Optional[Timestamp] = None,
    max_access_count: Optional[int] = None,
    emails: Optional[Sequence[str]] = None,
    disabled: bool = False,
    hide_email: Optional[bool] = None,
  ) -> Union[SendSchema, Any]:
    """Create a Send.

    Only Text Sends are supported.

    ``disabled`` is always in the request, because Vaultwarden refuses a
    Send without it.

    Args:
        name: Name of the Send.
        text: The text the Send shares.
        hidden: Hide the text until the recipient chooses to show it.
        notes: Private notes, not shown to the recipient.
        password: Password the recipient must enter to open the Send.
        deletion_date: When the server deletes the Send; timezone-aware.
        expiration_date: When the Send stops opening; timezone-aware.
        max_access_count: How many times the Send may be opened.
        emails: Valid email addresses the Send is restricted to.
        disabled: Create the Send disabled. Sent even when false.
        hide_email: Hide your email address from the recipient.

    Returns:
        The created Send, with its server-assigned id and access URL.
    """
    body = _template(
      name, text, hidden, notes, password, deletion_date, expiration_date, max_access_count, emails, disabled, hide_email
    )

    return self._request("POST", "/object/send", body=(SendTemplateSchema, body), response_type=SendSchema)

  # ---------------------------------------------------------------------------
  @route("PUT", "/object/send/{id}")
  def modify(
    self: Sends,
    send_id: SendId,
    name: str,
    text: str,
    *,
    hidden: bool = False,
    notes: Optional[str] = None,
    password: Optional[Password] = None,
    deletion_date: Optional[Timestamp] = None,
    expiration_date: Optional[Timestamp] = None,
    max_access_count: Optional[int] = None,
    emails: Optional[Sequence[str]] = None,
    disabled: bool = False,
    hide_email: Optional[bool] = None,
  ) -> Union[SendSchema, Any]:
    """Edit a Send.

    Only Text Sends are supported.

    The arguments are those of ``add``, and the whole Send is replaced, so
    pass every value to keep. In particular ``disabled`` is always sent
    and defaults to ``False``: modifying a disabled Send without
    ``disabled=True`` enables it again.

    Args:
        send_id: Unique identifier of the Send to edit.
        name: Name of the Send.
        text: The text the Send shares.
        hidden: Hide the text until the recipient chooses to show it.
        notes: Private notes, not shown to the recipient.
        password: Password the recipient must enter to open the Send.
        deletion_date: When the server deletes the Send; timezone-aware.
        expiration_date: When the Send stops opening; timezone-aware.
        max_access_count: How many times the Send may be opened.
        emails: Addresses the Send is restricted to.
        disabled: Keep or make the Send disabled.
        hide_email: Hide your email address from the recipient.

    Returns:
        The updated Send.
    """
    body = _template(
      name, text, hidden, notes, password, deletion_date, expiration_date, max_access_count, emails, disabled, hide_email
    )

    return self._request(
      "PUT",
      "/object/send/{id}",
      path_params=(ObjectSendIdPutParameters, {
        "id": send_id
      }),
      body=(SendTemplateSchema, body),
      response_type=SendSchema,
    )

  # ---------------------------------------------------------------------------
  @route("GET", "/object/send/{id}")
  def get(self: Sends, send_id: SendId) -> Union[SendSchema, Any]:
    """Retrieve a Send.

    Only Text Sends are supported.

    Args:
        send_id: Unique identifier of the Send.

    Returns:
        The Send.
    """
    return self._request(
      "GET", "/object/send/{id}", path_params=(ObjectSendIdGetParameters, {
        "id": send_id
      }), response_type=SendSchema
    )

  # ---------------------------------------------------------------------------
  @route("DELETE", "/object/send/{id}")
  def delete(self: Sends, send_id: SendId) -> Any:
    """Delete a Send.

    Only Text Sends are supported.

    Args:
        send_id: Unique identifier of the Send.

    Returns:
        ``None``, or the error handler's return value.
    """
    return self._request("DELETE", "/object/send/{id}", path_params=(ObjectSendIdDeleteParameters, {"id": send_id}))

  # ---------------------------------------------------------------------------
  @route("GET", "/list/object/send")
  def list(self: Sends, search: Optional[str] = None) -> Union[list[SendSchema], Any]:
    """Retrieve a list of Sends.

    Only Text Sends are supported.

    Args:
        search: Narrows the list to Sends matching it. When ``None`` or
            empty, every Send is returned.

    Returns:
        The matching Sends (empty if none match).
    """
    query = (ListObjectSendGetParameters, {"search": search or None})

    return self._request("GET", "/list/object/send", query=query, response_type=list[SendSchema])

  # ---------------------------------------------------------------------------
  @route("POST", "/send/{id}/remove-password")
  def remove_password(self: Sends, send_id: SendId) -> Union[SendSchema, Any]:
    """Remove the password from a Send.

    Only Text Sends are supported.

    Args:
        send_id: Unique identifier of the Send.

    Returns:
        The Send, now without a password (``password_set`` is false).
    """
    return self._request(
      "POST",
      "/send/{id}/remove-password",
      path_params=(SendIdRemovePasswordPostParameters, {
        "id": send_id
      }),
      response_type=SendSchema,
    )
