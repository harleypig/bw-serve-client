"""Folders domain class for the Bitwarden Vault Management API.

Mirrors the ``Folders`` tag in the API spec. One method per route:

  POST   /object/folder       - Folders.add
  PUT    /object/folder/{id}  - Folders.modify
  GET    /object/folder/{id}  - Folders.get
  DELETE /object/folder/{id}  - Folders.delete
  GET    /list/object/folders - Folders.list
"""

from __future__ import annotations

import logging
from typing import Any, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from .api_client import ApiClient, ValidationError
from .models import FolderSchema

FolderId = Union[UUID, str]


class Folder(BaseModel):
  """A folder as returned by the Vault Management API.

  ``FolderSchema`` from ``models.py`` describes the request body
  (``{"name": ...}``). The API responds with id + name + object, which
  the generator does not produce a schema for, so it is modelled here.

  Attributes:
      id: Server-assigned unique identifier.
      name: Folder name.
      object: API object discriminator; always ``"folder"``.
  """

  model_config = ConfigDict(populate_by_name=True)

  id: UUID
  name: str
  object: str = "folder"


class Folders:
  """Folder operations on a Bitwarden vault.

  Args:
      client: Shared :class:`ApiClient` for HTTP transport.
      logger: Optional logger; falls back to a module logger.
      error_handler: Optional injected error handler per the
          *Error / Logging Module Contract* in ``WORKFLOW.md``. When
          ``None``, errors propagate as exceptions raised by
          :class:`ApiClient`.
  """

  # ---------------------------------------------------------------------------
  def __init__(
    self: "Folders",
    client: ApiClient,
    logger: Optional[logging.Logger] = None,
    error_handler: Optional[Any] = None,
  ) -> None:
    self._client = client
    self._log = logger or logging.getLogger(__name__)
    self._errors = error_handler

  # ---------------------------------------------------------------------------
  # POST /object/folder
  def add(self: "Folders", name: str) -> Folder:
    """Add a folder to your vault.

    Args:
        name: Name of the folder to create. Must be non-empty.

    Returns:
        The created :class:`Folder` with its server-assigned id.

    Raises:
        ValidationError: If ``name`` is empty or whitespace-only.
    """
    if not name or not name.strip():
      raise ValidationError("folder name must be non-empty")

    body = FolderSchema(name=name).model_dump(exclude_none=True, by_alias=True)

    self._log.debug("POST /object/folder name=%r", name)
    resp = self._client.post("/object/folder", data=body)

    return Folder.model_validate(resp["data"])

  # ---------------------------------------------------------------------------
  # PUT /object/folder/{id}
  def modify(self: "Folders", folder_id: FolderId, name: str) -> Folder:
    """Edit an existing folder.

    Args:
        folder_id: Unique identifier of the folder to edit.
        name: New name for the folder. Must be non-empty.

    Returns:
        The updated :class:`Folder`.

    Raises:
        ValidationError: If ``name`` is empty or whitespace-only.
    """
    if not name or not name.strip():
      raise ValidationError("folder name must be non-empty")

    body = FolderSchema(name=name).model_dump(exclude_none=True, by_alias=True)

    self._log.debug("PUT /object/folder/%s name=%r", folder_id, name)
    resp = self._client.put(f"/object/folder/{folder_id}", data=body)

    return Folder.model_validate(resp["data"])

  # ---------------------------------------------------------------------------
  # GET /object/folder/{id}
  def get(self: "Folders", folder_id: FolderId) -> Folder:
    """Retrieve a folder by id.

    Args:
        folder_id: Unique identifier of the folder.

    Returns:
        The :class:`Folder`.
    """
    self._log.debug("GET /object/folder/%s", folder_id)
    resp = self._client.get(f"/object/folder/{folder_id}")

    return Folder.model_validate(resp["data"])

  # ---------------------------------------------------------------------------
  # DELETE /object/folder/{id}
  def delete(self: "Folders", folder_id: FolderId) -> None:
    """Delete a folder by id.

    Deleting a folder does NOT delete the items in it; the API moves
    them to "no folder".

    Args:
        folder_id: Unique identifier of the folder.
    """
    self._log.debug("DELETE /object/folder/%s", folder_id)
    self._client.delete(f"/object/folder/{folder_id}")

  # ---------------------------------------------------------------------------
  # GET /list/object/folders
  def list(self: "Folders", search: Optional[str] = None) -> list[Folder]:
    """List folders, optionally filtered by a search term.

    Args:
        search: Substring match against folder names. When ``None`` or
            empty, all folders are returned.

    Returns:
        List of matching :class:`Folder` objects (empty if none match).
    """
    params = {"search": search} if search else None

    self._log.debug("GET /list/object/folders params=%r", params)
    resp = self._client.get("/list/object/folders", params=params)

    return [Folder.model_validate(f) for f in resp["data"]["data"]]
