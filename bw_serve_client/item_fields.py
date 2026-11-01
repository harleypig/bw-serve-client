"""ItemFields domain class for the Bitwarden Vault Management API.

Single-field getters for a vault item, from the ``Attachments & Fields``
tag in the API spec. One method per route, named for the field it reads:

  GET /object/username/{id} - ItemFields.username
  GET /object/password/{id} - ItemFields.password
  GET /object/uri/{id}      - ItemFields.uri
  GET /object/totp/{id}     - ItemFields.totp
  GET /object/notes/{id}    - ItemFields.notes
  GET /object/exposed/{id}  - ItemFields.exposed
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING, Union
from uuid import UUID

from ._generated.models import ObjectExposedIdGetParameters
from ._generated.models import ObjectNotesIdGetParameters
from ._generated.models import ObjectPasswordIdGetParameters
from ._generated.models import ObjectTotpIdGetParameters
from ._generated.models import ObjectUriIdGetParameters
from ._generated.models import ObjectUsernameIdGetParameters
from ._generated.models import SecretStringResponseSchema
from ._generated.models import StringResponseSchema
from .errors import ExternalServiceError
from .resource import Resource
from .resource import route

if TYPE_CHECKING:
  from pydantic import BaseModel
  from pydantic import SecretStr

ItemId = Union[UUID, str]


class ItemFields(Resource):
  """Read one field of a vault item at a time.

  The spec types every ``{id}`` as a UUID, so an item is named by its id;
  the search term ``bw get`` accepts in its place is refused before
  sending. Construction, logging and error handling are
  :class:`Resource`'s. Every method returns what the error handler
  returned, in place of its result, when a failure is handled without
  raising.
  """

  # ---------------------------------------------------------------------------
  def _field(
    self: ItemFields, path: str, parameters: type[BaseModel], item_id: ItemId,
    response_type: type[Union[StringResponseSchema, SecretStringResponseSchema]]
  ) -> Any:
    """Fetch one field and unwrap it from its string envelope.

    Args:
        path: The route's path template.
        parameters: The route's path-parameter model.
        item_id: Unique identifier of the item.
        response_type: ``StringResponseSchema`` or ``SecretStringResponseSchema``.

    Returns:
        The envelope's ``data``, or the error handler's return value.
    """
    result = self._request("GET", path, path_params=(parameters, {"id": item_id}), response_type=response_type)

    return self._member(result, response_type, "data")

  # ---------------------------------------------------------------------------
  @route("GET", "/object/username/{id}")
  def username(self: ItemFields, item_id: ItemId) -> Union[str, Any]:
    """Retrieve the username of a login item.

    Args:
        item_id: Unique identifier of the item.

    Returns:
        The login's username.
    """
    return self._field("/object/username/{id}", ObjectUsernameIdGetParameters, item_id, StringResponseSchema)

  # ---------------------------------------------------------------------------
  @route("GET", "/object/password/{id}")
  def password(self: ItemFields, item_id: ItemId) -> Union[SecretStr, Any]:
    """Retrieve the password of a login item.

    Args:
        item_id: Unique identifier of the item.

    Returns:
        The login's password; ``get_secret_value()`` reveals it.
    """
    return self._field("/object/password/{id}", ObjectPasswordIdGetParameters, item_id, SecretStringResponseSchema)

  # ---------------------------------------------------------------------------
  @route("GET", "/object/uri/{id}")
  def uri(self: ItemFields, item_id: ItemId) -> Union[str, Any]:
    """Retrieve the URI of a login item.

    Args:
        item_id: Unique identifier of the item.

    Returns:
        The login's first URI.
    """
    return self._field("/object/uri/{id}", ObjectUriIdGetParameters, item_id, StringResponseSchema)

  # ---------------------------------------------------------------------------
  @route("GET", "/object/totp/{id}")
  def totp(self: ItemFields, item_id: ItemId) -> Union[SecretStr, Any]:
    """Retrieve the TOTP code of a login item.

    Args:
        item_id: Unique identifier of the item.

    Returns:
        The current TOTP code; ``get_secret_value()`` reveals it.
    """
    return self._field("/object/totp/{id}", ObjectTotpIdGetParameters, item_id, SecretStringResponseSchema)

  # ---------------------------------------------------------------------------
  @route("GET", "/object/notes/{id}")
  def notes(self: ItemFields, item_id: ItemId) -> Union[str, Any]:
    """Retrieve the notes of an item.

    Args:
        item_id: Unique identifier of the item.

    Returns:
        The item's notes.
    """
    return self._field("/object/notes/{id}", ObjectNotesIdGetParameters, item_id, StringResponseSchema)

  # ---------------------------------------------------------------------------
  @route("GET", "/object/exposed/{id}")
  def exposed(self: ItemFields, item_id: ItemId) -> Union[int, Any]:
    """Retrieve the number of times a password has been exposed for a login item.

    bw serve sends the count as a string; it is returned as an ``int``.

    Args:
        item_id: Unique identifier of the item.

    Returns:
        How many known breaches the login's password appears in.
    """
    result = self._request(
      "GET",
      "/object/exposed/{id}",
      path_params=(ObjectExposedIdGetParameters, {
        "id": item_id
      }),
      response_type=StringResponseSchema
    )

    if not isinstance(result, StringResponseSchema):
      return result

    try:
      return int(result.data or "")

    except ValueError:
      return self._fail(ExternalServiceError, f"exposed count is not an integer: {result.data!r}")
