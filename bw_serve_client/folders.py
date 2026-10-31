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

from ._generated.models import FolderSchema
from ._generated.models import ListObjectFoldersGetParameters
from ._generated.models import ObjectFolderIdDeleteParameters
from ._generated.models import ObjectFolderIdGetParameters
from ._generated.models import ObjectFolderIdPutParameters
from .errors import ValidationError
from .resource import Resource

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

  # bw lists "No Folder" with a null id; it must not fail the whole list.
  id: Optional[UUID]
  name: str
  object: str = "folder"


class Folders(Resource):
  """Folder operations on a Bitwarden vault.

  Construction, logging and error handling are :class:`Resource`'s. Every
  method returns what the error handler returned, in place of its result,
  when a failure is handled without raising.
  """

  # ---------------------------------------------------------------------------
  # POST /object/folder
  def add(self: Folders, name: str) -> Union[Folder, Any]:
    """Add a folder to your vault.

    Args:
        name: Name of the folder to create. Must be non-empty.

    Returns:
        The created :class:`Folder` with its server-assigned id.
    """
    if not name or not name.strip():
      return self._fail(ValidationError, "folder name must be non-empty")

    return self._request("POST", "/object/folder", body=(FolderSchema, {"name": name}), response_type=Folder)

  # ---------------------------------------------------------------------------
  # PUT /object/folder/{id}
  def modify(self: Folders, folder_id: FolderId, name: str) -> Union[Folder, Any]:
    """Edit an existing folder.

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
  # GET /object/folder/{id}
  def get(self: Folders, folder_id: FolderId) -> Union[Folder, Any]:
    """Retrieve a folder by id.

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
  # DELETE /object/folder/{id}
  def delete(self: Folders, folder_id: FolderId) -> Any:
    """Delete a folder by id.

    Deleting a folder does NOT delete the items in it; the API moves
    them to "no folder".

    Args:
        folder_id: Unique identifier of the folder.

    Returns:
        ``None``, or the error handler's return value.
    """
    return self._request("DELETE", "/object/folder/{id}", path_params=(ObjectFolderIdDeleteParameters, {"id": folder_id}))

  # ---------------------------------------------------------------------------
  # GET /list/object/folders
  def list(self: Folders, search: Optional[str] = None) -> Union[list[Folder], Any]:
    """List folders, optionally filtered by a search term.

    Args:
        search: Substring match against folder names. When ``None`` or
            empty, all folders are returned.

    Returns:
        List of matching :class:`Folder` objects (empty if none match).
    """
    query = (ListObjectFoldersGetParameters, {"search": search or None})

    return self._request("GET", "/list/object/folders", query=query, response_type=list[Folder])
