"""Tests for the Attachments domain class."""

from __future__ import annotations

from email.parser import BytesParser
from email.policy import default
import io
from typing import Any, Optional, TYPE_CHECKING
from uuid import uuid4

from conftest import load_recorded
import httpx
import pytest

from bw_serve_client._generated.models import ItemSchema
from bw_serve_client.api_client import ApiClient
from bw_serve_client.attachments import Attachments
from bw_serve_client.errors import ExternalServiceError
from bw_serve_client.errors import ValidationError

if TYPE_CHECKING:
  from pathlib import Path

  from conftest import MakeClient
  from conftest import ReturningHandler

CREATE = load_recorded("attachment-create")
ITEM_ID = CREATE["response"]["body"]["data"]["id"]
ATTACHMENT_ID = CREATE["response"]["body"]["data"]["attachments"][0]["id"]

#: Every byte value, so no decoding of a download can pass it unchanged
#: unless it is no decoding at all.
BINARY = bytes(range(256))


# -----------------------------------------------------------------------------
def _uploaded(request: httpx.Request) -> tuple[Optional[str], bytes]:
  """Read the multipart ``file`` part of an upload request.

  Args:
    request: A sent request with a multipart/form-data body.

  Returns:
    The part's file name and its content.
  """
  header = f"Content-Type: {request.headers['Content-Type']}\r\n\r\n".encode()
  message = BytesParser(policy=default).parsebytes(header + request.content)
  [part] = [part for part in message.iter_parts() if part.get_param("name", header="content-disposition") == "file"]
  content = part.get_payload(decode=True)
  assert isinstance(content, bytes)

  return part.get_filename(), content


# -----------------------------------------------------------------------------
def _storing_client() -> ApiClient:
  """Build an ApiClient whose transport keeps an upload and serves it back.

  A POST stores the uploaded file and answers with the recorded item; any
  other request answers with the stored file as a download.

  Returns:
    The client.
  """
  stored: dict[str, bytes] = {}

  def handler(request: httpx.Request) -> httpx.Response:
    if request.method == "POST":
      stored["file"] = _uploaded(request)[1]
      return httpx.Response(200, json=CREATE["response"]["body"])

    return httpx.Response(200, content=stored["file"], headers={"Content-Type": "application/octet-stream"})

  return ApiClient(transport=httpx.MockTransport(handler))


# -----------------------------------------------------------------------------
def _file_client(sent: list[httpx.Request], content: bytes, content_type: Optional[str] = "application/octet-stream") -> ApiClient:
  """Build an ApiClient whose transport answers every request with a file.

  Args:
    sent: Where each request is recorded.
    content: The response body.
    content_type: The response Content-Type; none when ``None``.

  Returns:
    The client.
  """
  headers = {"Content-Type": content_type} if content_type is not None else {}

  def handler(request: httpx.Request) -> httpx.Response:
    sent.append(request)
    return httpx.Response(200, content=content, headers=headers)

  return ApiClient(transport=httpx.MockTransport(handler))


# -----------------------------------------------------------------------------
class TestAttachmentsAdd:
  """Tests for Attachments.add."""

  def test_posts_multipart_file_with_itemid_query(
    self: TestAttachmentsAdd, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """POST /attachment sends the file as multipart and returns the item."""
    attachments = Attachments(make_client(json_body=CREATE["response"]["body"]))

    result = attachments.add(ITEM_ID, b"Made-up attachment.\n", "recorded-attachment.txt")  # act

    [request] = sent
    file_name, content = _uploaded(request)
    assert request.method == "POST"
    assert request.url.path == "/attachment"
    assert request.url.params["itemid"] == ITEM_ID
    assert request.headers["Content-Type"].startswith("multipart/form-data; boundary=")
    assert (file_name, content) == ("recorded-attachment.txt", b"Made-up attachment.\n")
    assert isinstance(result, ItemSchema)
    assert str(result.id) == ITEM_ID
    assert result.attachments is not None
    assert result.attachments[0].id == ATTACHMENT_ID

  def test_sends_no_authentication(self: TestAttachmentsAdd, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """No Authorization header goes out: bw serve has no endpoint auth."""
    attachments = Attachments(make_client(json_body=CREATE["response"]["body"]))

    attachments.add(ITEM_ID, b"x", "x.txt")  # act

    [request] = sent
    assert "Authorization" not in request.headers

  def test_reads_a_path_named_by_its_base_name(
    self: TestAttachmentsAdd, tmp_path: Path, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """A path is read in binary and stored under its base name."""
    path = tmp_path / "photo.bin"
    path.write_bytes(BINARY)
    attachments = Attachments(make_client(json_body=CREATE["response"]["body"]))

    attachments.add(ITEM_ID, str(path))  # act

    assert _uploaded(sent[0]) == ("photo.bin", BINARY)

  def test_path_object_with_explicit_name(
    self: TestAttachmentsAdd, tmp_path: Path, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """A ``Path`` is accepted, and ``file_name`` overrides its base name."""
    path = tmp_path / "local.txt"
    path.write_bytes(b"notes")
    attachments = Attachments(make_client(json_body=CREATE["response"]["body"]))

    attachments.add(ITEM_ID, path, file_name="stored.txt")  # act

    assert _uploaded(sent[0]) == ("stored.txt", b"notes")

  def test_sends_a_file_object(self: TestAttachmentsAdd, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A binary file object is sent as it is."""
    attachments = Attachments(make_client(json_body=CREATE["response"]["body"]))

    attachments.add(ITEM_ID, io.BytesIO(BINARY), "blob.dat")  # act

    assert _uploaded(sent[0]) == ("blob.dat", BINARY)

  @pytest.mark.parametrize("file_name", [None, ""])
  def test_content_without_a_name_is_refused(
    self: TestAttachmentsAdd, file_name: Optional[str], make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """Bytes with no file name raise ValidationError before sending."""
    attachments = Attachments(make_client())

    with pytest.raises(ValidationError, match="file name is required"):
      attachments.add(ITEM_ID, b"data", file_name)

    assert sent == []

  def test_missing_path_is_refused(
    self: TestAttachmentsAdd, tmp_path: Path, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """A path that cannot be read raises ValidationError before sending."""
    attachments = Attachments(make_client())

    with pytest.raises(ValidationError, match="cannot read the attachment") as exc_info:
      attachments.add(ITEM_ID, tmp_path / "absent.txt")

    assert isinstance(exc_info.value.__cause__, FileNotFoundError)
    assert sent == []

  def test_path_without_a_base_name_is_refused(
    self: TestAttachmentsAdd, tmp_path: Path, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """A path ending in a separator has no name to store the file under."""
    attachments = Attachments(make_client())

    with pytest.raises(ValidationError, match="no file name"):
      attachments.add(ITEM_ID, f"{tmp_path}/")

    assert sent == []

  def test_rejects_non_uuid_item_id(self: TestAttachmentsAdd, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """An item id that is not a UUID raises ValidationError before sending."""
    attachments = Attachments(make_client())

    with pytest.raises(ValidationError, match="invalid query"):
      attachments.add("not-a-uuid", b"data", "a.txt")

    assert sent == []

  def test_server_error_is_external_service_error(self: TestAttachmentsAdd, make_client: MakeClient) -> None:
    """The recorded 500 for an upload with no file is an ExternalServiceError."""
    recorded = load_recorded("attachment-no-file")["response"]
    attachments = Attachments(make_client(status=recorded["status"], text_body=recorded["body"]))

    with pytest.raises(ExternalServiceError, match="Internal Server Error") as exc_info:
      attachments.add(ITEM_ID, b"data", "a.txt")

    assert exc_info.value.status_code == 500

  def test_response_not_an_item_is_external_service_error(self: TestAttachmentsAdd, make_client: MakeClient) -> None:
    """A success whose data is not an item fails parsing."""
    attachments = Attachments(make_client(json_body={"success": True, "data": {"id": "not-a-uuid"}}))

    with pytest.raises(ExternalServiceError, match="response does not match"):
      attachments.add(ITEM_ID, b"data", "a.txt")

  def test_returning_handler_value_is_returned(
    self: TestAttachmentsAdd, make_client: MakeClient, returning_handler: ReturningHandler
  ) -> None:
    """A handler that returns instead of raising supplies the result."""
    attachments = Attachments(make_client(), error_handler=returning_handler)

    result = attachments.add(ITEM_ID, b"data")  # act

    assert result is returning_handler.result
    assert [call[0] for call in returning_handler.calls] == [ValidationError]


# -----------------------------------------------------------------------------
class TestAttachmentsGet:
  """Tests for Attachments.get."""

  def test_gets_the_recorded_file(self: TestAttachmentsGet, sent: list[httpx.Request]) -> None:
    """GET /object/attachment/{id}?itemid= returns the body as bytes."""
    recorded = load_recorded("attachment-get")
    attachments = Attachments(_file_client(sent, recorded["response"]["body"].encode()))

    result = attachments.get(ATTACHMENT_ID, ITEM_ID)  # act

    [request] = sent
    assert request.method == "GET"
    assert f"{request.url.path}?{request.url.query.decode()}" == recorded["request"]["path"]
    assert "Authorization" not in request.headers
    assert result == b"Made-up attachment for fixture recording.\n"

  # bw serve labels every download application/octet-stream, but the body
  # is the file whatever the label, so a text type must not decode it.
  @pytest.mark.parametrize("content_type", ["application/octet-stream", "text/plain; charset=utf-8", None])
  def test_binary_survives_download(self: TestAttachmentsGet, content_type: Optional[str], sent: list[httpx.Request]) -> None:
    """Bytes that are not valid UTF-8 come back unchanged."""
    attachments = Attachments(_file_client(sent, BINARY, content_type))

    result = attachments.get(ATTACHMENT_ID, ITEM_ID)  # act

    assert result == BINARY

  def test_upload_then_download_round_trip(self: TestAttachmentsGet, tmp_path: Path) -> None:
    """What is uploaded from a file comes back from get byte for byte."""
    path = tmp_path / "binary.dat"
    path.write_bytes(BINARY)
    attachments = Attachments(_storing_client())
    attachments.add(ITEM_ID, path)

    result = attachments.get(ATTACHMENT_ID, ITEM_ID)  # act

    assert result == BINARY

  @pytest.mark.parametrize("attachment_id", ["6e30f37acb730272aa86", "o4lrz575u84koanvu9f5gqv9a9ab92gf", str(uuid4())])
  def test_accepts_non_uuid_attachment_ids(self: TestAttachmentsGet, attachment_id: str, sent: list[httpx.Request]) -> None:
    """Vaultwarden's hex ids, Bitwarden's alphanumeric ids and UUIDs pass."""
    attachments = Attachments(_file_client(sent, b"x"))

    attachments.get(attachment_id, ITEM_ID)  # act

    assert sent[0].url.path == f"/object/attachment/{attachment_id}"

  @pytest.mark.parametrize("attachment_id", ["", "../object/item", "a/b", "a?b", "a b"])
  def test_rejects_unsafe_attachment_ids(self: TestAttachmentsGet, attachment_id: str, sent: list[httpx.Request]) -> None:
    """An id that would change the path raises ValidationError before sending."""
    attachments = Attachments(_file_client(sent, b"x"))

    with pytest.raises(ValidationError, match="invalid path"):
      attachments.get(attachment_id, ITEM_ID)

    assert sent == []

  def test_rejects_non_uuid_item_id(self: TestAttachmentsGet, sent: list[httpx.Request]) -> None:
    """An item id that is not a UUID raises ValidationError before sending."""
    attachments = Attachments(_file_client(sent, b"x"))

    with pytest.raises(ValidationError, match=r"invalid path .*: itemid: "):
      attachments.get(ATTACHMENT_ID, "not-a-uuid")

    assert sent == []

  def test_deleted_attachment_is_validation_error(self: TestAttachmentsGet, make_client: MakeClient) -> None:
    """The recorded 400 for a deleted attachment is a ValidationError."""
    recorded = load_recorded("attachment-get-deleted")["response"]
    attachments = Attachments(make_client(status=recorded["status"], json_body=recorded["body"]))

    with pytest.raises(ValidationError, match="No attachments available for this item.") as exc_info:
      attachments.get(ATTACHMENT_ID, ITEM_ID)

    assert exc_info.value.status_code == 400

  def test_returning_handler_value_is_returned(
    self: TestAttachmentsGet, make_client: MakeClient, returning_handler: ReturningHandler
  ) -> None:
    """A handled 400 returns the handler's value, not bytes."""
    recorded = load_recorded("attachment-get-deleted")["response"]
    client = make_client(status=recorded["status"], json_body=recorded["body"])
    attachments = Attachments(client, error_handler=returning_handler)

    result = attachments.get(ATTACHMENT_ID, ITEM_ID)  # act

    assert result is returning_handler.result
    assert returning_handler.calls[0][:3] == (ValidationError, "No attachments available for this item.", 400)


# -----------------------------------------------------------------------------
class TestAttachmentsDelete:
  """Tests for Attachments.delete."""

  def test_deletes_returns_none(self: TestAttachmentsDelete, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """DELETE /object/attachment/{id}?itemid= returns None."""
    recorded = load_recorded("attachment-delete")
    attachments = Attachments(make_client(json_body=recorded["response"]["body"]))

    result = attachments.delete(ATTACHMENT_ID, ITEM_ID)  # act

    [request] = sent
    assert result is None
    assert request.method == "DELETE"
    assert f"{request.url.path}?{request.url.query.decode()}" == recorded["request"]["path"]
    assert "Authorization" not in request.headers

  def test_rejects_unsafe_attachment_id(self: TestAttachmentsDelete, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """An id with a path separator raises ValidationError before sending."""
    attachments = Attachments(make_client())

    with pytest.raises(ValidationError, match="invalid path"):
      attachments.delete("a/b", ITEM_ID)

    assert sent == []

  def test_rejects_non_uuid_item_id(self: TestAttachmentsDelete, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """An item id that is not a UUID raises ValidationError before sending."""
    attachments = Attachments(make_client())

    with pytest.raises(ValidationError, match=r"invalid path .*: itemid: "):
      attachments.delete(ATTACHMENT_ID, "not-a-uuid")

    assert sent == []

  def test_error_goes_to_injected_handler(
    self: TestAttachmentsDelete, make_client: MakeClient, returning_handler: ReturningHandler
  ) -> None:
    """A 400 goes to the resource's handler, whose value is returned."""
    client = make_client(status=400, json_body={"success": False, "message": "Not found."})
    attachments = Attachments(client, error_handler=returning_handler)

    result: Any = attachments.delete(ATTACHMENT_ID, ITEM_ID)  # act

    assert result is returning_handler.result
    assert returning_handler.calls[0][:3] == (ValidationError, "Not found.", 400)
