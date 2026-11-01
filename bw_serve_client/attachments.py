"""Attachments domain class for the Bitwarden Vault Management API.

Mirrors the ``Attachments`` tag in the API spec. One method per route:

  POST   /attachment              - Attachments.add
  GET    /object/attachment/{id}  - Attachments.get
  DELETE /object/attachment/{id}  - Attachments.delete
"""

from __future__ import annotations

import os
from typing import Annotated, Any, BinaryIO, Optional, Union
from uuid import UUID

import httpx
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from ._generated.models import AttachmentPostParameters
from ._generated.models import ItemSchema
from .errors import ValidationError
from .resource import Resource
from .resource import route

ItemId = Union[UUID, str]

#: What :meth:`Attachments.add` uploads: a path to read, or the content.
FileSource = Union[str, os.PathLike[str], bytes, BinaryIO]

# The generated get and delete parameter models type the attachment id as
# a UUID, which it is not (Vaultwarden's are 20 hex characters, Bitwarden's
# 32 lower-case alphanumerics). So the path is validated by this model, and
# the itemid query by the upload's model, which holds that one field.
_ItemQuery = AttachmentPostParameters


class _AttachmentPath(BaseModel):
  """The ``{id}`` path parameter of the attachment routes.

  Attributes:
      id: The attachment id; letters, digits and hyphens only, since it is
          put into the path unescaped.
      model_config: Rejects unknown fields.
  """

  model_config = ConfigDict(extra="forbid")

  id: Annotated[str, Field(pattern=r"^[A-Za-z0-9-]+$")]


class Attachments(Resource):
  """Attachment operations on a Bitwarden vault.

  Construction, logging and error handling are :class:`Resource`'s. Every
  method returns what the error handler returned, in place of its result,
  when a failure is handled without raising.
  """

  # ---------------------------------------------------------------------------
  @route("POST", "/attachment")
  def add(self: Attachments, item_id: ItemId, file: FileSource, file_name: Optional[str] = None) -> Union[ItemSchema, Any]:
    """Attach a file to an existing vault item.

    The file goes up as multipart form data. A path is opened and streamed;
    bytes and binary file objects are sent as they are, and need a
    ``file_name``.

    Args:
        item_id: Unique identifier of the item to attach the file to.
        file: A path, or the content as ``bytes`` or a binary file object.
        file_name: Stored name; defaults to the path's base name.

    Returns:
        The item, as :class:`ItemSchema`, with the new attachment listed.
    """
    if isinstance(file, (str, os.PathLike)):
      name = file_name if file_name is not None else os.path.basename(file)

      if not name:
        return self._fail(ValidationError, f"no file name for the attachment: {os.fspath(file)!r} has no base name")

      try:
        with open(file, "rb") as handle:
          return self._upload(item_id, name, handle)

      except OSError as e:
        return self._fail(ValidationError, f"cannot read the attachment {os.fspath(file)!r}: {e.strerror}", cause=e)

    if not file_name:
      return self._fail(ValidationError, "a file name is required to attach bytes or a file object")

    return self._upload(item_id, file_name, file)

  # ---------------------------------------------------------------------------
  def _upload(self: Attachments, item_id: ItemId, file_name: str, content: Union[bytes, BinaryIO]) -> Union[ItemSchema, Any]:
    """Send one attachment upload.

    Args:
        item_id: Unique identifier of the item.
        file_name: Name the attachment is stored under.
        content: The file's bytes, or an open binary file.

    Returns:
        The updated item, or the error handler's return value.
    """
    return self._request(
      "POST",
      "/attachment",
      query=(_ItemQuery, {
        "itemid": item_id
      }),
      files={"file": (file_name, content)},
      response_type=ItemSchema,
    )

  # ---------------------------------------------------------------------------
  @route("GET", "/object/attachment/{id}")
  def get(self: Attachments, attachment_id: str, item_id: ItemId) -> Union[bytes, Any]:
    """Retrieve an attachment.

    If you're retrieving any file type other than plaintext, we recommend
    posting the request through a browser window for immediate download.

    That advice is for a browser; here every file type comes back as its
    exact bytes, whatever its content.

    Args:
        attachment_id: The attachment's id, as listed in the item's
            ``attachments``; not a UUID.
        item_id: Unique identifier of the item the attachment is on.

    Returns:
        The file's content.
    """
    return self._request(
      "GET",
      "/object/attachment/{id}",
      path_params=(_AttachmentPath, {
        "id": attachment_id
      }),
      query=(_ItemQuery, {
        "itemid": item_id
      }),
      response_type=bytes,
    )

  # ---------------------------------------------------------------------------
  @route("DELETE", "/object/attachment/{id}")
  def delete(self: Attachments, attachment_id: str, item_id: ItemId) -> Any:
    """Delete an attachment.

    Args:
        attachment_id: The attachment's id; not a UUID.
        item_id: Unique identifier of the item the attachment is on.

    Returns:
        ``None``, or the error handler's return value.
    """
    return self._request(
      "DELETE",
      "/object/attachment/{id}",
      path_params=(_AttachmentPath, {
        "id": attachment_id
      }),
      query=(_ItemQuery, {
        "itemid": item_id
      }),
    )

  # ---------------------------------------------------------------------------
  def _parse(self: Attachments, response: httpx.Response, response_type: Any) -> Any:
    """Parse a 2xx response; a download is the body's bytes, not an envelope.

    The body is read raw rather than by content type: the file is the whole
    body whatever header it carries, and decoding it as text would corrupt
    anything that is not UTF-8.

    Args:
        response: A successful response.
        response_type: ``bytes`` for a download, else a model for ``data``.

    Returns:
        The file's bytes, or ``Resource._parse``'s result.
    """
    if response_type is bytes:
      return response.content

    return super()._parse(response, response_type)
