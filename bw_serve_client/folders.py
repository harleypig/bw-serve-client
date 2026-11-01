"""Folders domain class for the Bitwarden Vault Management API.

Mirrors the ``Folders`` tag in the API spec. One method per route:

  POST   /object/folder       - Folders.add
  PUT    /object/folder/{id}  - Folders.modify
  GET    /object/folder/{id}  - Folders.get
  DELETE /object/folder/{id}  - Folders.delete
  GET    /list/object/folders - Folders.list
"""

from __future__ import annotations

from typing import Any, Optional, Union
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import field_validator

from ._generated.models import FolderSchema
from ._generated.models import ListObjectFoldersGetParameters
from ._generated.models import ObjectFolderIdDeleteParameters
from ._generated.models import ObjectFolderIdGetParameters
from ._generated.models import ObjectFolderIdPutParameters
from .errors import ValidationError
from .resource import Resource
from .resource import route

FolderId = Union[UUID, str]


class Folder(BaseModel):
  """A folder as returned by the Vault Management API.

  The generated ``FolderSchema`` describes the request body
  (``{"name": ...}``). The API responds with id + name + object, which
  the generator does not produce a schema for, so it is modelled here.

  Attributes:
      id: Server-assigned unique identifier; ``None`` for "No Folder".
      name: Folder name.
      object: API object discriminator; always ``"folder"``.
      model_config: Accepts field names as well as aliases.
  """

  model_config = ConfigDict(populate_by_name=True)

  # bw lists "No Folder" with an empty-string id; it must not fail the
  # whole list, so the empty string is read as no id.
  id: Optional[UUID]
  name: str
  object: str = "folder"

  # ---------------------------------------------------------------------------
  @field_validator("id", mode="before")
  @classmethod
  def _empty_id_is_none(cls: type[Folder], value: Any) -> Any:
    """Read the empty-string id bw serve gives "No Folder" as ``None``.

    Args:
        value: The raw id.

    Returns:
        ``None`` for an empty string, otherwise the value unchanged.
    """
    return None if value == "" else value


class Folders(Resource):
  """Folder operations on a Bitwarden vault.

  Construction, logging and error handling are :class:`Resource`'s. Every
  method returns what the error handler returned, in place of its result,
  when a failure is handled without raising.
  """

  # ---------------------------------------------------------------------------
  @route("POST", "/object/folder")
  def add(self: Folders, name: str) -> Union[Folder, Any]:
    """Add a folder to your vault.

    Args:
        name: Name of the folder to create. bw serve accepts an empty
            name, so this does too.

    Returns:
        The created :class:`Folder` with its server-assigned id.
    """
    return self._request("POST", "/object/folder", body=(FolderSchema, {"name": name}), response_type=Folder)

  # ---------------------------------------------------------------------------
  @route("PUT", "/object/folder/{id}")
  def modify(self: Folders, folder_id: FolderId, name: str) -> Union[Folder, Any]:
    """Edit a folder in your vault.

    Args:
        folder_id: Unique identifier of the folder to edit.
        name: New name for the folder. Must be non-empty.

    Returns:
        The updated :class:`Folder`.
    """
    if not name or not name.strip():
      return self._fail(ValidationError, "folder name must be non-empty")

    return self._request(
      "PUT",
      "/object/folder/{id}",
      path_params=(ObjectFolderIdPutParameters, {
        "id": folder_id
      }),
      body=(FolderSchema, {
        "name": name
      }),
      response_type=Folder,
    )

  # ---------------------------------------------------------------------------
  @route("GET", "/object/folder/{id}")
  def get(self: Folders, folder_id: FolderId) -> Union[Folder, Any]:
    """Retrieve a folder from your vault.

    Args:
        folder_id: Unique identifier of the folder.

    Returns:
        The :class:`Folder`.
    """
    return self._request(
      "GET", "/object/folder/{id}", path_params=(ObjectFolderIdGetParameters, {
        "id": folder_id
      }), response_type=Folder
    )

  # ---------------------------------------------------------------------------
  @route("DELETE", "/object/folder/{id}")
  def delete(self: Folders, folder_id: FolderId) -> Any:
    """Delete a folder from your vault.

    Deleting a folder will not delete the items in it. bw serve moves
    them to "No Folder".

    Args:
        folder_id: Unique identifier of the folder.

    Returns:
        ``None``, or the error handler's return value.
    """
    return self._request("DELETE", "/object/folder/{id}", path_params=(ObjectFolderIdDeleteParameters, {"id": folder_id}))

  # ---------------------------------------------------------------------------
  @route("GET", "/list/object/folders")
  def list(self: Folders, search: Optional[str] = None) -> Union[list[Folder], Any]:
    """Retrieve a list of folders in your vault.

    A search term narrows the list to folders whose names match it.

    Args:
        search: Substring match against folder names. When ``None`` or
            empty, all folders are returned.

    Returns:
        List of matching :class:`Folder` objects (empty if none match).
    """
    query = (ListObjectFoldersGetParameters, {"search": search or None})

    return self._request("GET", "/list/object/folders", query=query, response_type=list[Folder])
