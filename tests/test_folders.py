"""Tests for the Folders domain class."""

from uuid import UUID
from uuid import uuid4

import pytest

from bw_serve_client.api_client import ValidationError
from bw_serve_client.folders import Folder
from bw_serve_client.folders import Folders


@pytest.fixture
def fake_client(mocker):
  """ApiClient stand-in. Tests wire .return_value as needed."""
  return mocker.Mock()


@pytest.fixture
def folders(fake_client):
  """Folders bound to a mocked ApiClient."""
  return Folders(fake_client)


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

    # Act
    result = Folder.model_validate(payload)

    # Assert
    assert isinstance(result.id, UUID)
    assert result.name == "Notes"
    assert result.object == "folder"


# -----------------------------------------------------------------------------
class TestFoldersAdd:
  """Tests for Folders.add."""

  def test_posts_to_object_folder_with_name_body(self: "TestFoldersAdd", fake_client, folders) -> None:
    """POST /object/folder with {name} body, returns parsed Folder."""
    # Arrange
    fake_id = uuid4()
    fake_client.post.return_value = {
      "success": True,
      "data": {
        "object": "folder",
        "id": str(fake_id),
        "name": "Notes",
      },
    }

    # Act
    result = folders.add(name="Notes")

    # Assert
    fake_client.post.assert_called_once_with("/object/folder", data={"name": "Notes"})
    assert isinstance(result, Folder)
    assert result.id == fake_id
    assert result.name == "Notes"

  def test_rejects_empty_name(self: "TestFoldersAdd", fake_client, folders) -> None:
    """Empty name raises ValidationError before hitting the wire."""
    # Arrange / Act / Assert
    with pytest.raises(ValidationError, match="non-empty"):
      folders.add(name="")

    fake_client.post.assert_not_called()

  def test_rejects_whitespace_only_name(self: "TestFoldersAdd", fake_client, folders) -> None:
    """Whitespace-only name raises ValidationError."""
    # Arrange / Act / Assert
    with pytest.raises(ValidationError, match="non-empty"):
      folders.add(name="   ")

    fake_client.post.assert_not_called()


# -----------------------------------------------------------------------------
class TestFoldersModify:
  """Tests for Folders.modify."""

  def test_puts_to_object_folder_id_with_name_body(self: "TestFoldersModify", fake_client, folders) -> None:
    """PUT /object/folder/{id} with {name} body, returns parsed Folder."""
    # Arrange
    fake_id = uuid4()
    fake_client.put.return_value = {
      "success": True,
      "data": {
        "object": "folder",
        "id": str(fake_id),
        "name": "Renamed",
      },
    }

    # Act
    result = folders.modify(fake_id, name="Renamed")

    # Assert
    fake_client.put.assert_called_once_with(f"/object/folder/{fake_id}", data={"name": "Renamed"})
    assert result.name == "Renamed"
    assert result.id == fake_id

  def test_accepts_string_folder_id(self: "TestFoldersModify", fake_client, folders) -> None:
    """folder_id can be a raw string; passed through into the URL."""
    # Arrange
    fake_id_str = "3a84be8d-12e7-4223-98cd-ae0000eabdec"
    fake_client.put.return_value = {
      "success": True,
      "data": {
        "object": "folder",
        "id": fake_id_str,
        "name": "Renamed",
      },
    }

    # Act
    folders.modify(fake_id_str, name="Renamed")

    # Assert
    fake_client.put.assert_called_once_with(f"/object/folder/{fake_id_str}", data={"name": "Renamed"})

  def test_rejects_empty_name(self: "TestFoldersModify", fake_client, folders) -> None:
    """Empty name raises ValidationError before hitting the wire."""
    # Arrange / Act / Assert
    with pytest.raises(ValidationError, match="non-empty"):
      folders.modify(uuid4(), name="")

    fake_client.put.assert_not_called()


# -----------------------------------------------------------------------------
class TestFoldersGet:
  """Tests for Folders.get."""

  def test_gets_object_folder_id_returns_parsed_folder(self: "TestFoldersGet", fake_client, folders) -> None:
    """GET /object/folder/{id} returns a parsed Folder."""
    # Arrange
    fake_id = uuid4()
    fake_client.get.return_value = {
      "success": True,
      "data": {
        "object": "folder",
        "id": str(fake_id),
        "name": "Existing",
      },
    }

    # Act
    result = folders.get(fake_id)

    # Assert
    fake_client.get.assert_called_once_with(f"/object/folder/{fake_id}")
    assert isinstance(result, Folder)
    assert result.id == fake_id
    assert result.name == "Existing"


# -----------------------------------------------------------------------------
class TestFoldersDelete:
  """Tests for Folders.delete."""

  def test_deletes_object_folder_id_returns_none(self: "TestFoldersDelete", fake_client, folders) -> None:
    """DELETE /object/folder/{id} returns None."""
    # Arrange
    fake_id = uuid4()

    # Act
    result = folders.delete(fake_id)

    # Assert
    assert result is None
    fake_client.delete.assert_called_once_with(f"/object/folder/{fake_id}")


# -----------------------------------------------------------------------------
class TestFoldersList:
  """Tests for Folders.list."""

  def test_list_without_search_sends_no_params(self: "TestFoldersList", fake_client, folders) -> None:
    """GET /list/object/folders with no params when search is None."""
    # Arrange
    fake_client.get.return_value = {
      "success": True,
      "data": {
        "object": "list",
        "data": [],
      },
    }

    # Act
    result = folders.list()

    # Assert
    fake_client.get.assert_called_once_with("/list/object/folders", params=None)
    assert result == []

  def test_list_with_search_passes_query_param(self: "TestFoldersList", fake_client, folders) -> None:
    """GET /list/object/folders forwards search as a query parameter."""
    # Arrange
    fake_client.get.return_value = {
      "success": True,
      "data": {
        "object": "list",
        "data": [
          {"object": "folder", "id": str(uuid4()), "name": "Personal"},
          {"object": "folder", "id": str(uuid4()), "name": "Personal Notes"},
        ],
      },
    }

    # Act
    result = folders.list(search="Personal")

    # Assert
    fake_client.get.assert_called_once_with("/list/object/folders", params={"search": "Personal"})
    assert len(result) == 2
    assert all(isinstance(f, Folder) for f in result)
    assert {f.name for f in result} == {"Personal", "Personal Notes"}

  def test_list_with_empty_search_omits_query_param(self: "TestFoldersList", fake_client, folders) -> None:
    """Empty search string is treated as no filter."""
    # Arrange
    fake_client.get.return_value = {
      "success": True,
      "data": {"object": "list", "data": []},
    }

    # Act
    folders.list(search="")

    # Assert
    fake_client.get.assert_called_once_with("/list/object/folders", params=None)


# -----------------------------------------------------------------------------
class TestFoldersInit:
  """Tests for Folders construction and DI hooks."""

  def test_uses_provided_logger(self: "TestFoldersInit", fake_client, mocker) -> None:
    """Injected logger is used for debug output."""
    # Arrange
    logger = mocker.Mock()
    folders = Folders(fake_client, logger=logger)
    fake_client.get.return_value = {
      "success": True,
      "data": {"object": "list", "data": []},
    }

    # Act
    folders.list()

    # Assert
    logger.debug.assert_called()

  def test_falls_back_to_module_logger(self: "TestFoldersInit", fake_client) -> None:
    """When no logger is provided, a module logger is created."""
    # Arrange / Act
    folders = Folders(fake_client)

    # Assert
    assert folders._log is not None
