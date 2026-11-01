"""Tests for the Folders domain class."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING
from uuid import UUID
from uuid import uuid4

import pytest

from bw_serve_client.errors import ValidationError
from bw_serve_client.folders import Folder
from bw_serve_client.folders import Folders

if TYPE_CHECKING:
  from conftest import MakeClient
  import httpx


def _folder(folder_id: object, name: str) -> dict[str, object]:
  """Build bw serve's success body for one folder.

  Args:
    folder_id: The folder's id.
    name: The folder's name.

  Returns:
    The response body.
  """
  return {"success": True, "data": {"object": "folder", "id": str(folder_id), "name": name}}


def _folders(*names: str) -> dict[str, object]:
  """Build bw serve's success body for a folder list.

  Args:
    names: One folder per name.

  Returns:
    The response body.
  """
  items = [{"object": "folder", "id": str(uuid4()), "name": name} for name in names]
  return {"success": True, "data": {"object": "list", "data": items}}


# -----------------------------------------------------------------------------
class TestFolderModel:
  """Tests for the Folder response model."""

  def test_coerces_string_id_to_uuid(self: "TestFolderModel") -> None:
    """Folder.id is a UUID even when the API returns a string."""
    # Arrange
    payload = {
      "id": "3a84be8d-12e7-4223-98cd-ae0000eabdec",
      "name": "Notes",
      "object": "folder",
    }

    result = Folder.model_validate(payload)  # act

    # Assert
    assert isinstance(result.id, UUID)
    assert result.name == "Notes"
    assert result.object == "folder"

  def test_empty_string_id_is_none(self: "TestFolderModel") -> None:
    """The empty-string id bw serve gives "No Folder" reads as None."""
    result = Folder.model_validate({"id": "", "name": "No Folder", "object": "folder"})  # act

    assert result.id is None


# -----------------------------------------------------------------------------
class TestFoldersAdd:
  """Tests for Folders.add."""

  def test_posts_to_object_folder_with_name_body(self: TestFoldersAdd, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """POST /object/folder with {name} body, returns parsed Folder."""
    fake_id = uuid4()
    folders = Folders(make_client(json_body=_folder(fake_id, "Notes")))

    result = folders.add(name="Notes")  # act

    [request] = sent
    assert request.method == "POST"
    assert request.url.path == "/object/folder"
    assert json.loads(request.content) == {"name": "Notes"}
    assert isinstance(result, Folder)
    assert result.id == fake_id
    assert result.name == "Notes"

  # bw serve accepts an empty name and creates the folder (the
  # folder-create-empty-name recording), so add sends it rather than refusing.
  @pytest.mark.parametrize("name", ["", "   "])
  def test_sends_empty_name(self: TestFoldersAdd, name: str, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """An empty or blank name is sent as given, not refused client-side."""
    folders = Folders(make_client(json_body=_folder(uuid4(), name)))

    result = folders.add(name=name)  # act

    [request] = sent
    assert json.loads(request.content) == {"name": name}
    assert result.name == name


# -----------------------------------------------------------------------------
class TestFoldersModify:
  """Tests for Folders.modify."""

  def test_puts_to_object_folder_id_with_name_body(
    self: TestFoldersModify, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """PUT /object/folder/{id} with {name} body, returns parsed Folder."""
    fake_id = uuid4()
    folders = Folders(make_client(json_body=_folder(fake_id, "Renamed")))

    result = folders.modify(fake_id, name="Renamed")  # act

    [request] = sent
    assert request.method == "PUT"
    assert request.url.path == f"/object/folder/{fake_id}"
    assert json.loads(request.content) == {"name": "Renamed"}
    assert result.name == "Renamed"
    assert result.id == fake_id

  def test_accepts_string_folder_id(self: TestFoldersModify, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A raw string folder_id is passed through into the URL."""
    fake_id_str = "3a84be8d-12e7-4223-98cd-ae0000eabdec"
    folders = Folders(make_client(json_body=_folder(fake_id_str, "Renamed")))

    folders.modify(fake_id_str, name="Renamed")  # act

    [request] = sent
    assert request.url.path == f"/object/folder/{fake_id_str}"

  def test_rejects_non_uuid_folder_id(self: TestFoldersModify, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A folder_id that is not a UUID raises ValidationError before sending."""
    folders = Folders(make_client())

    with pytest.raises(ValidationError, match="invalid path"):
      folders.modify("not-a-uuid", name="Renamed")

    assert sent == []

  # Matches add: bw serve accepts an empty name on create, so modify sends
  # one rather than refusing it client-side.
  @pytest.mark.parametrize("name", ["", "   "])
  def test_sends_empty_name(self: TestFoldersModify, name: str, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """An empty or blank name is sent as given, not refused client-side."""
    fake_id = uuid4()
    folders = Folders(make_client(json_body=_folder(fake_id, name)))

    result = folders.modify(fake_id, name=name)  # act

    [request] = sent
    assert json.loads(request.content) == {"name": name}
    assert result.name == name


# -----------------------------------------------------------------------------
class TestFoldersGet:
  """Tests for Folders.get."""

  def test_gets_object_folder_id_returns_parsed_folder(
    self: TestFoldersGet, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """GET /object/folder/{id} returns a parsed Folder."""
    fake_id = uuid4()
    folders = Folders(make_client(json_body=_folder(fake_id, "Existing")))

    result = folders.get(fake_id)  # act

    [request] = sent
    assert request.method == "GET"
    assert request.url.path == f"/object/folder/{fake_id}"
    assert isinstance(result, Folder)
    assert result.id == fake_id
    assert result.name == "Existing"

  def test_not_found_raises_validation_error(self: TestFoldersGet, make_client: MakeClient) -> None:
    """Bw serve's 400 "Not found." is a ValidationError carrying the status."""
    folders = Folders(make_client(status=400, json_body={"success": False, "message": "Not found."}))

    with pytest.raises(ValidationError, match="Not found.") as exc_info:
      folders.get(uuid4())

    assert exc_info.value.status_code == 400


# -----------------------------------------------------------------------------
class TestFoldersDelete:
  """Tests for Folders.delete."""

  def test_deletes_object_folder_id_returns_none(
    self: TestFoldersDelete, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """DELETE /object/folder/{id} returns None."""
    fake_id = uuid4()
    folders = Folders(make_client(json_body={"success": True}))

    result = folders.delete(fake_id)  # act

    [request] = sent
    assert result is None
    assert request.method == "DELETE"
    assert request.url.path == f"/object/folder/{fake_id}"


# -----------------------------------------------------------------------------
class TestFoldersList:
  """Tests for Folders.list."""

  def test_list_without_search_sends_no_params(self: TestFoldersList, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """GET /list/object/folders with no params when search is None."""
    folders = Folders(make_client(json_body=_folders()))

    result = folders.list()  # act

    [request] = sent
    assert request.url.path == "/list/object/folders"
    assert request.url.query == b""
    assert result == []

  def test_list_with_search_passes_query_param(self: TestFoldersList, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """GET /list/object/folders forwards search as a query parameter."""
    folders = Folders(make_client(json_body=_folders("Personal", "Personal Notes")))

    result = folders.list(search="Personal")  # act

    [request] = sent
    assert request.url.params["search"] == "Personal"
    assert len(result) == 2
    assert all(isinstance(f, Folder) for f in result)
    assert {f.name for f in result} == {"Personal", "Personal Notes"}

  def test_list_accepts_no_folder_entry(self: TestFoldersList, make_client: MakeClient) -> None:
    """The "No Folder" entry, whose id is empty, parses beside the real folders."""
    body = _folders("Personal")
    body["data"]["data"].append({"object": "folder", "id": "", "name": "No Folder"})  # type: ignore[index]
    folders = Folders(make_client(json_body=body))

    result = folders.list()  # act

    assert [(f.name, f.id is None) for f in result] == [("Personal", False), ("No Folder", True)]

  def test_list_with_empty_search_omits_query_param(
    self: TestFoldersList, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """Empty search string is treated as no filter."""
    folders = Folders(make_client(json_body=_folders()))

    folders.list(search="")  # act

    [request] = sent
    assert request.url.query == b""


# -----------------------------------------------------------------------------
class TestFoldersInit:
  """Tests for Folders construction and DI hooks."""

  def test_uses_provided_logger(self: TestFoldersInit, make_client: MakeClient, caplog: pytest.LogCaptureFixture) -> None:
    """Injected logger is used for debug output."""
    folders = Folders(make_client(json_body=_folders()), logger=logging.getLogger("test.folders"))

    with caplog.at_level(logging.DEBUG, logger="test.folders"):  # act
      folders.list()

    assert any(r.name == "test.folders" for r in caplog.records)

  def test_falls_back_to_client_logger(self: TestFoldersInit, make_client: MakeClient) -> None:
    """When no logger is provided, the client's logger is used."""
    client = make_client()

    folders = Folders(client)  # act

    assert folders.logger is client.logger
