"""Tests for ApiClient module."""

from __future__ import annotations

import http.server
import json
import logging
import socketserver
import tempfile
import threading
from typing import Any, List, Optional, Tuple, TYPE_CHECKING
from unittest.mock import Mock
from unittest.mock import patch

import httpx
import pytest

from bw_serve_client.api_client import ApiClient
from bw_serve_client.errors import DefaultErrorHandler
from bw_serve_client.errors import ExternalServiceError
from bw_serve_client.errors import InternalError
from bw_serve_client.errors import UserError
from bw_serve_client.errors import ValidationError

if TYPE_CHECKING:
  from conftest import ReturningHandler
  from pytest_mock import MockerFixture


class TestApiClient:
  """Test cases for ApiClient class."""

  def test_init_default_values(self: "TestApiClient") -> None:
    """Test ApiClient initialization with default values."""
    # Arrange

    client = ApiClient()  # act

    # Assert
    assert client.base_url == "http://localhost:8087"
    assert client.timeout == 30
    assert client.session is not None

  def test_init_custom_values(self: "TestApiClient") -> None:
    """Test ApiClient initialization with custom values."""
    # Arrange
    logger = Mock()

    client = ApiClient(protocol="http", domain="test", port=8080, timeout=60, logger=logger)  # act

    # Assert
    assert client.base_url == "http://test:8080"
    assert client.timeout == 60
    assert client.logger == logger

  def test_init_custom_user_agent(self: "TestApiClient") -> None:
    """Test ApiClient initialization with custom user agent."""
    # Arrange

    client = ApiClient(user_agent="MyApp/2.0.0")  # act

    # Assert
    assert client.session.headers['User-Agent'] == "MyApp/2.0.0"

  def test_init_default_user_agent(self: "TestApiClient") -> None:
    """Test ApiClient initialization with default user agent."""
    # Arrange

    client = ApiClient()  # act

    # Assert
    assert client.session.headers['User-Agent'] == "bw-serve-client/0.1.1"

  def test_init_with_individual_parameters(self: "TestApiClient") -> None:
    """Test ApiClient initialization with individual parameters."""
    # Arrange

    client = ApiClient(protocol="https", domain="api.example.com", port=443, path="/v1")  # act

    # Assert
    assert client.base_url == "https://api.example.com:443/v1"
    assert client.timeout == 30

  def test_init_with_individual_parameters_defaults(self: "TestApiClient") -> None:
    """Test ApiClient initialization with individual parameters using defaults."""
    # Arrange

    client = ApiClient(protocol="https", domain="secure.example.com")  # act

    # Assert
    assert client.base_url == "https://secure.example.com:8087"
    assert client.timeout == 30

  def test_init_with_path_only(self: "TestApiClient") -> None:
    """Test ApiClient initialization with custom path only."""
    # Arrange

    client = ApiClient(path="/api/v2")  # act

    # Assert
    assert client.base_url == "http://localhost:8087/api/v2"

  def test_serialize_data_json(self: "TestApiClient") -> None:
    """Test JSON data serialization."""
    # Arrange
    client = ApiClient()
    data = {"key": "value"}

    result = client._serialize_data(data, "application/json")  # act

    # Assert
    assert result == data

  def test_serialize_data_string(self: "TestApiClient") -> None:
    """Test string data serialization."""
    # Arrange
    client = ApiClient()
    data = '{"key": "value"}'

    result = client._serialize_data(data, "application/json")  # act

    # Assert
    assert result == {"key": "value"}

  def test_serialize_data_multipart(self: "TestApiClient") -> None:
    """Test multipart data serialization."""
    # Arrange
    client = ApiClient()
    data = {"file": "content"}

    result = client._serialize_data(data, "multipart/form-data")  # act

    # Assert
    assert result == data

  def test_deserialize_data_json(self: "TestApiClient") -> None:
    """Test JSON response deserialization."""
    # Arrange
    client = ApiClient()
    response = Mock()
    response.headers = {"content-type": "application/json"}
    response.json.return_value = {"key": "value"}

    result = client._deserialize_data(response)  # act

    # Assert
    assert result == {"key": "value"}

  def test_deserialize_data_text(self: "TestApiClient") -> None:
    """Test text response deserialization."""
    client = ApiClient()
    response = Mock()
    response.headers = {"content-type": "text/plain"}
    response.text = "plain text"

    result = client._deserialize_data(response)  # act

    assert result == "plain text"

  def test_handle_error_401(self: "TestApiClient") -> None:
    """Test error handling for 401 Unauthorized."""
    client = ApiClient()
    response = Mock()
    response.status_code = 401
    response.json.return_value = {"message": "Unauthorized"}

    with pytest.raises(UserError, match="Unauthorized"):  # act
      client._handle_error(response)

  def test_handle_error_400(self: "TestApiClient") -> None:
    """Test error handling for 400 Bad Request."""
    client = ApiClient()
    response = Mock()
    response.status_code = 400
    response.json.return_value = {"message": "Bad Request"}

    with pytest.raises(ValidationError, match="Bad Request"):  # act
      client._handle_error(response)

  def test_handle_error_404(self: "TestApiClient") -> None:
    """Test error handling for 404 Not Found."""
    client = ApiClient()
    response = Mock()
    response.status_code = 404
    response.json.return_value = {"message": "Not Found"}

    with pytest.raises(ValidationError, match="Not Found") as exc_info:  # act
      client._handle_error(response)

    assert exc_info.value.status_code == 404

  def test_handle_error_500(self: "TestApiClient") -> None:
    """Test error handling for 500 Server Error."""
    client = ApiClient()
    response = Mock()
    response.status_code = 500
    response.json.return_value = {"message": "Server Error"}

    with pytest.raises(ExternalServiceError, match="Server Error"):  # act
      client._handle_error(response)

  def test_get_request(self: "TestApiClient") -> None:
    """Test GET request method."""
    client, seen = _recording_client(json_body={"data": "test"})

    result = client.get("/test", params={"key": "value"})  # act

    [request] = seen
    assert request.method == "GET"
    assert str(request.url) == "http://localhost:8087/test?key=value"
    assert request.headers["Accept"] == "application/json"
    assert request.headers["User-Agent"] == "bw-serve-client/0.1.1"
    assert request.content == b""
    assert result == {"data": "test"}

  def test_post_request(self: "TestApiClient") -> None:
    """Test POST request method."""
    client, seen = _recording_client(json_body={"created": True})
    data = {"name": "test"}

    result = client.post("/test", data=data)  # act

    [request] = seen
    assert request.method == "POST"
    assert str(request.url) == "http://localhost:8087/test"
    assert request.headers["Content-Type"] == "application/json"
    assert json.loads(request.content) == data
    assert result == {"created": True}

  def test_post_request_with_files(self: "TestApiClient") -> None:
    """Test POST request method with file upload."""
    client, seen = _recording_client(json_body={"uploaded": True})
    data = {"name": "test"}
    files = {"file": ("note.txt", b"file content")}

    result = client.post("/test", data=data, files=files)  # act

    [request] = seen
    assert request.headers["Content-Type"].startswith("multipart/form-data; boundary=")
    assert b'name="name"' in request.content
    assert b'filename="note.txt"' in request.content
    assert b"file content" in request.content
    assert result == {"uploaded": True}

  def test_context_manager(self: "TestApiClient") -> None:
    """Test context manager functionality."""
    with ApiClient() as client:  # act
      assert not client.session.is_closed

    assert client.session.is_closed

  def test_close(self: "TestApiClient") -> None:
    """Test close method."""
    client = ApiClient()

    client.close()  # act

    assert client.session.is_closed

  def test_serialize_data_invalid_json(self: "TestApiClient") -> None:
    """Test JSON data serialization with invalid JSON string."""
    client = ApiClient()
    data = '{"invalid": json}'  # Invalid JSON

    result = client._serialize_data(data, "application/json")  # act

    assert result == data  # Should return original string

  def test_serialize_data_other_content_type(self: "TestApiClient") -> None:
    """Test data serialization with other content type."""
    client = ApiClient()
    data = {"key": "value"}

    result = client._serialize_data(data, "text/plain")  # act

    assert result == str(data)

  def test_serialize_data_none(self: "TestApiClient") -> None:
    """Test data serialization with None data."""
    client = ApiClient()

    result = client._serialize_data(None, "application/json")  # act

    assert result is None

  def test_serialize_data_list(self: "TestApiClient") -> None:
    """Test data serialization with list data."""
    client = ApiClient()
    data = [1, 2, 3, {"nested": "value"}]

    result = client._serialize_data(data, "application/json")  # act

    assert result == data

  def test_serialize_data_nested_dict(self: "TestApiClient") -> None:
    """Test data serialization with nested dictionary."""
    client = ApiClient()
    data = {"level1": {"level2": {"level3": "deep_value", "array": [1, 2, 3]}}}

    result = client._serialize_data(data, "application/json")  # act

    assert result == data

  def test_serialize_data_empty_string(self: "TestApiClient") -> None:
    """Test data serialization with empty string."""
    client = ApiClient()

    result = client._serialize_data("", "application/json")  # act

    assert result == ""

  def test_serialize_data_whitespace_string(self: "TestApiClient") -> None:
    """Test data serialization with whitespace-only string."""
    client = ApiClient()

    result = client._serialize_data("   ", "application/json")  # act

    assert result == "   "

  def test_serialize_data_unicode_string(self: "TestApiClient") -> None:
    """Test data serialization with unicode string."""
    client = ApiClient()
    data = '{"unicode": "测试", "emoji": "🚀"}'

    result = client._serialize_data(data, "application/json")  # act

    expected = {"unicode": "测试", "emoji": "🚀"}
    assert result == expected

  def test_deserialize_data_json_decode_error(self: "TestApiClient") -> None:
    """Test JSON response deserialization with decode error."""
    client = ApiClient()
    response = Mock()
    response.headers = {"content-type": "application/json"}
    response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
    response.text = "invalid json"

    result = client._deserialize_data(response)  # act

    assert result == "invalid json"

  def test_deserialize_data_empty_response(self: "TestApiClient") -> None:
    """Test deserialization with empty response."""
    client = ApiClient()
    response = Mock()
    response.headers = {"content-type": "application/json"}
    response.json.return_value = {}
    response.text = ""

    result = client._deserialize_data(response)  # act

    assert result == {}

  def test_deserialize_data_none_response(self: "TestApiClient") -> None:
    """Test deserialization with None response."""
    client = ApiClient()
    response = Mock()
    response.headers = {"content-type": "application/json"}
    response.json.return_value = None
    response.text = ""

    result = client._deserialize_data(response)  # act

    assert result is None

  def test_deserialize_data_list_response(self: "TestApiClient") -> None:
    """Test deserialization with list response."""
    client = ApiClient()
    response = Mock()
    response.headers = {"content-type": "application/json"}
    response.json.return_value = [1, 2, 3, {"key": "value"}]
    response.text = ""

    result = client._deserialize_data(response)  # act

    expected_result: list[dict[str, str] | int] = [1, 2, 3, {"key": "value"}]
    assert result == expected_result

  def test_deserialize_data_nested_response(self: "TestApiClient") -> None:
    """Test deserialization with nested data response."""
    client = ApiClient()
    response = Mock()
    response.headers = {"content-type": "application/json"}
    nested_data = {"level1": {"level2": {"level3": "deep_value", "array": [1, 2, 3]}}}
    response.json.return_value = nested_data
    response.text = ""

    result = client._deserialize_data(response)  # act

    assert result == nested_data

  def test_deserialize_data_unicode_response(self: "TestApiClient") -> None:
    """Test deserialization with unicode data response."""
    client = ApiClient()
    response = Mock()
    response.headers = {"content-type": "application/json"}
    unicode_data = {"unicode": "测试", "emoji": "🚀"}
    response.json.return_value = unicode_data
    response.text = ""

    result = client._deserialize_data(response)  # act

    assert result == unicode_data

  def test_deserialize_data_mixed_content_type(self: "TestApiClient") -> None:
    """Test deserialization with mixed content type header."""
    client = ApiClient()
    response = Mock()
    response.headers = {"content-type": "application/json; charset=utf-8"}
    response.json.return_value = {"key": "value"}
    response.text = ""

    result = client._deserialize_data(response)  # act

    assert result == {"key": "value"}

  def test_deserialize_data_no_content_type(self: "TestApiClient") -> None:
    """Test deserialization with no content type header."""
    client = ApiClient()
    response = Mock()
    response.headers = {}
    response.text = "plain text response"

    result = client._deserialize_data(response)  # act

    assert result == "plain text response"

  def test_deserialize_data_xml_content_type(self: "TestApiClient") -> None:
    """Test deserialization with XML content type."""
    client = ApiClient()
    response = Mock()
    response.headers = {"content-type": "application/xml"}
    response.text = "<root><item>value</item></root>"

    result = client._deserialize_data(response)  # act

    assert result == "<root><item>value</item></root>"

  def test_handle_error_json_decode_error(self: "TestApiClient") -> None:
    """Test error handling with JSON decode error."""
    client = ApiClient()
    response = Mock()
    response.status_code = 400
    response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
    response.text = "Bad Request"

    with pytest.raises(ValidationError, match="Bad Request"):  # act
      client._handle_error(response)

  def test_handle_error_no_message_key(self: "TestApiClient") -> None:
    """Test error handling with no 'message' key in error data."""
    client = ApiClient()
    response = Mock()
    response.status_code = 400
    response.json.return_value = {"error": "Bad Request"}  # No 'message' key
    response.text = "Bad Request"

    with pytest.raises(ValidationError, match="API request failed with status 400"):  # act
      client._handle_error(response)

  def test_handle_error_key_error(self: "TestApiClient") -> None:
    """Test error handling with KeyError in error data processing."""
    client = ApiClient()
    response = Mock()
    response.status_code = 400
    # Make response.json() raise a KeyError when called
    response.json.side_effect = KeyError("message")
    response.text = "Bad Request"

    with pytest.raises(ValidationError, match="Bad Request"):  # act
      client._handle_error(response)

  def test_handle_error_other_status_code(self: "TestApiClient") -> None:
    """Test error handling for other status codes."""
    client = ApiClient()
    response = Mock()
    response.status_code = 418  # I'm a teapot
    response.json.return_value = {"message": "I'm a teapot"}

    with pytest.raises(ValidationError, match="I'm a teapot"):  # act
      client._handle_error(response)

  def test_make_request_with_headers(self: "TestApiClient") -> None:
    """Test _make_request with custom headers."""
    client, seen = _recording_client(json_body={"data": "test"})
    custom_headers = {"Authorization": "Bearer token"}

    client._make_request("GET", "/test", headers=custom_headers)  # act

    [request] = seen
    assert request.headers["Authorization"] == "Bearer token"
    assert request.headers["Accept"] == "application/json"
    assert request.headers["User-Agent"] == "bw-serve-client/0.1.1"

  def test_make_request_exception(self: "TestApiClient") -> None:
    """Test _make_request with a transport error."""
    client = ApiClient(transport=httpx.MockTransport(_refuse))

    with pytest.raises(ExternalServiceError, match="Request failed: Connection failed") as exc_info:  # act
      client._make_request("GET", "/test")

    assert isinstance(exc_info.value.__cause__, httpx.ConnectError)

  @pytest.mark.parametrize(
    ("status", "error"),
    [(400, ValidationError), (401, UserError), (403, UserError), (404, ValidationError), (500, ExternalServiceError),
     (418, ValidationError)],
  )
  def test_make_request_error_status(self: "TestApiClient", status: int, error: type) -> None:
    """An error status from the server raises its domain error, keeping the status."""
    client, _ = _recording_client(status=status, json_body={"message": "nope"})

    with pytest.raises(error, match="nope") as exc_info:  # act
      client.get("/test")

    assert exc_info.value.status_code == status

  @pytest.mark.parametrize("message", ["Vault is locked.", "You are not logged in."])
  def test_locked_vault_400_is_user_error(self: "TestApiClient", message: str) -> None:
    """Bw serve's 400 for a locked vault or no login is a user-side error."""
    client, _ = _recording_client(status=400, json_body={"success": False, "message": message})

    with pytest.raises(UserError, match=message) as exc_info:  # act
      client.get("/list/object/folders")

    assert exc_info.value.status_code == 400

  def test_put_request(self: "TestApiClient") -> None:
    """Test PUT request method."""
    client, seen = _recording_client(json_body={"updated": True})
    data = {"name": "updated"}

    result = client.put("/test", data=data)  # act

    [request] = seen
    assert request.method == "PUT"
    assert str(request.url) == "http://localhost:8087/test"
    assert json.loads(request.content) == data
    assert result == {"updated": True}

  def test_delete_request(self: "TestApiClient") -> None:
    """Test DELETE request method."""
    client, seen = _recording_client(json_body={"deleted": True})

    result = client.delete("/test")  # act

    [request] = seen
    assert request.method == "DELETE"
    assert str(request.url) == "http://localhost:8087/test"
    assert request.content == b""
    assert result == {"deleted": True}

  def test_serialization_integration_post(self: "TestApiClient") -> None:
    """Test serialization integration with POST request."""
    client, seen = _recording_client(json_body={"created": True})
    complex_data = {
      "user": {
        "name": "Test User",
        "settings": {
          "theme": "dark",
          "notifications": True
        },
        "tags": ["admin", "user"]
      },
      "metadata": {
        "created_at": "2023-01-01T00:00:00Z",
        "version": 1
      }
    }

    result = client.post("/users", data=complex_data)  # act

    [request] = seen
    assert json.loads(request.content) == complex_data
    assert result == {"created": True}

  def test_deserialization_integration_get(self: "TestApiClient") -> None:
    """Test deserialization integration with GET request."""
    complex_response = {
      "data": [
        {
          "id": 1,
          "name": "Item 1",
          "attributes": {
            "color": "red",
            "size": "large"
          },
        },
        {
          "id": 2,
          "name": "Item 2",
          "attributes": {
            "color": "blue",
            "size": "small"
          },
        },
      ],
      "pagination": {
        "page": 1,
        "total": 2,
        "per_page": 10
      }
    }
    client, _ = _recording_client(json_body=complex_response)

    result = client.get("/items")  # act

    assert result == complex_response

  def test_serialization_string_data_post(self: "TestApiClient") -> None:
    """Test serialization with string data in POST request."""
    client, seen = _recording_client(json_body={"processed": True})
    json_string = '{"name": "test", "value": 123}'

    result = client.post("/process", data=json_string)  # act

    # The string is parsed by _serialize_data and sent as a JSON object.
    [request] = seen
    assert json.loads(request.content) == {"name": "test", "value": 123}
    assert result == {"processed": True}

  def test_deserialization_error_fallback(self: "TestApiClient") -> None:
    """Test deserialization error fallback to text."""
    client, _ = _recording_client(text_body="Invalid JSON response", content_type="application/json")

    result = client.get("/test")  # act

    assert result == "Invalid JSON response"

  @patch('bw_serve_client.api_client.ApiClient._serialize_data')
  def test_serialize_data_called_in_post(self: "TestApiClient", mock_serialize: Mock) -> None:
    """Test that _serialize_data is called during POST requests."""
    mock_serialize.return_value = {"name": "test"}
    client, _ = _recording_client(json_body={"created": True})
    data = {"name": "test"}

    client.post("/test", data=data)  # act

    mock_serialize.assert_called_once_with(data, "application/json")

  @patch('bw_serve_client.api_client.ApiClient._serialize_data')
  def test_serialize_data_called_in_put(self: "TestApiClient", mock_serialize: Mock) -> None:
    """Test that _serialize_data is called during PUT requests."""
    mock_serialize.return_value = {"name": "updated"}
    client, _ = _recording_client(json_body={"updated": True})
    data = {"name": "updated"}

    client.put("/test", data=data)  # act

    mock_serialize.assert_called_once_with(data, "application/json")

  # httpx still sends a str passed as data=, with a DeprecationWarning; the
  # filter is what tells content= from data= here.
  @pytest.mark.filterwarnings("error::DeprecationWarning")
  def test_serialize_data_with_custom_content_type(self: "TestApiClient") -> None:
    """A non-JSON content type sends the serialized text as the raw body."""
    client, seen = _recording_client(text_body="Success", content_type="text/plain")
    data = {"name": "test"}

    result = client._make_request("POST", "/test", data=data, headers={"Content-Type": "text/plain"})  # act

    [request] = seen
    assert request.headers["Content-Type"] == "text/plain"
    assert request.content == str(data).encode()
    assert result.text == "Success"

  def test_make_request_unsupported_method(self: "TestApiClient") -> None:
    """Test that _make_request raises error for unsupported HTTP methods."""
    client = ApiClient()

    with pytest.raises(InternalError) as exc_info:  # act
      client._make_request("PATCH", "/test")

    assert "Unsupported HTTP method: PATCH" in str(exc_info.value)
    assert "Supported methods are: DELETE, GET, POST, PUT" in str(exc_info.value)

  def test_make_request_case_insensitive_method(self: "TestApiClient") -> None:
    """Test that _make_request accepts case-insensitive HTTP methods."""
    client, seen = _recording_client(json_body={"success": True})

    result = client._make_request("get", "/test")  # act

    [request] = seen
    assert result.status_code == 200
    assert request.method == "GET"
    assert str(request.url) == "http://localhost:8087/test"


class TestApiClientConnection:
  """How the client reaches bw serve: URL, Unix socket, or a transport."""

  def test_base_url_replaces_components(self: "TestApiClientConnection") -> None:
    """A base_url is used instead of the URL built from its parts."""
    client, seen = _recording_client(json_body={}, base_url="https://vault.example:9000/")

    client.get("/status")  # act

    [request] = seen
    assert client.base_url == "https://vault.example:9000"
    assert str(request.url) == "https://vault.example:9000/status"

  def test_default_transport_retries_connections(self: "TestApiClientConnection", mocker: MockerFixture) -> None:
    """The default transport retries failed connections max_retries times."""
    transport = mocker.patch('bw_serve_client.api_client.httpx.HTTPTransport', return_value=httpx.MockTransport(_ok))

    ApiClient(max_retries=5)  # act

    transport.assert_called_once_with(retries=5)

  def test_socket_transport(self: "TestApiClientConnection", mocker: MockerFixture) -> None:
    """A unix:// base_url builds a socket transport with the retry count."""
    transport = mocker.patch('bw_serve_client.api_client.httpx.HTTPTransport', return_value=httpx.MockTransport(_ok))

    client = ApiClient(base_url="unix:///run/bw.sock", port=8123, max_retries=2)  # act

    transport.assert_called_once_with(uds="/run/bw.sock", retries=2)
    assert client.base_url == "http://localhost:8123"

  # Port 80 is the case the explicit Host header exists for: httpx alone
  # drops a default port from the Host it derives from the URL.
  @pytest.mark.parametrize("port", [8087, 80])
  def test_socket_round_trip(self: "TestApiClientConnection", port: int, monkeypatch: pytest.MonkeyPatch) -> None:
    """A request over a real Unix socket reaches the server with Host: localhost:<port>."""
    # A relative socket path keeps under the AF_UNIX path limit (~108
    # bytes) however long TMPDIR is.
    with tempfile.TemporaryDirectory() as tmp:
      monkeypatch.chdir(tmp)
      server = _UnixHTTPServer("bw.sock", _EchoHostHandler)
      thread = threading.Thread(target=server.serve_forever, daemon=True)
      thread.start()

      try:
        with ApiClient(base_url="unix://bw.sock", port=port) as client:
          result = client.get("/status")  # act

      finally:
        server.shutdown()
        server.server_close()
        thread.join()
        monkeypatch.undo()

    assert result == {"host": f"localhost:{port}", "path": "/status"}

  def test_socket_url_without_path_raises(self: "TestApiClientConnection") -> None:
    """Unix:// with no socket path is rejected."""
    with pytest.raises(ValueError, match="no socket path"):  # act
      ApiClient(base_url="unix://")

  def test_socket_url_with_transport_raises(self: "TestApiClientConnection") -> None:
    """A socket URL and a caller's transport are mutually exclusive."""
    with pytest.raises(ValueError, match="not both"):  # act
      ApiClient(base_url="unix:///run/bw.sock", transport=httpx.MockTransport(_ok))

  def test_caller_transport_used_as_is(self: "TestApiClientConnection") -> None:
    """A caller's transport carries every request, and no Host override is set."""
    client, seen = _recording_client(json_body={"ok": True}, domain="vault", port=9000)

    result = client.get("/status")  # act

    [request] = seen
    assert request.headers["Host"] == "vault:9000"
    assert result == {"ok": True}


class TestApiClientErrorHandling:
  """Failures go through the injected or default error handler."""

  def test_default_logger_is_left_unconfigured(self: "TestApiClientErrorHandling") -> None:
    """Without a logger, the module logger is used with no handler or level set."""
    client = ApiClient()  # act

    assert client.logger is logging.getLogger("bw_serve_client.api_client")
    assert client.logger.handlers == []
    assert client.logger.level == logging.NOTSET

  def test_default_handler_logs_to_client_logger(self: "TestApiClientErrorHandling") -> None:
    """The default handler is a DefaultErrorHandler on the client's logger."""
    logger = logging.getLogger("test.api_client.injected")

    client = ApiClient(logger=logger)  # act

    assert isinstance(client.error_handler, DefaultErrorHandler)
    assert client.error_handler.logger is logger

  def test_returning_handler_result_replaces_response(
    self: "TestApiClientErrorHandling", returning_handler: ReturningHandler
  ) -> None:
    """A handler that returns has its value come back from the request method."""
    handler = returning_handler
    client, _ = _recording_client(status=500, json_body={"message": "boom"}, error_handler=handler)

    result = client.get("/test")  # act

    assert result is handler.result
    assert handler.calls == [(ExternalServiceError, "boom", 500, None)]

  def test_returning_handler_receives_transport_failure(
    self: "TestApiClientErrorHandling", returning_handler: ReturningHandler
  ) -> None:
    """A transport failure reaches the handler with its cause."""
    handler = returning_handler
    client = ApiClient(transport=httpx.MockTransport(_refuse), error_handler=handler)

    result = client.get("/test")  # act

    assert result is handler.result
    [(category, _, status_code, cause)] = handler.calls
    assert category is ExternalServiceError
    assert status_code is None
    assert isinstance(cause, httpx.ConnectError)

  def test_per_request_handler_overrides_client_handler(
    self: "TestApiClientErrorHandling", returning_handler: ReturningHandler
  ) -> None:
    """A handler passed to one request is used instead of the client's."""
    client, _ = _recording_client(status=404, json_body={"message": "Not found."})
    handler = returning_handler

    result = client._make_request("GET", "/test", error_handler=handler)  # act

    assert result is handler.result
    assert handler.calls == [(ValidationError, "Not found.", 404, None)]


# -----------------------------------------------------------------------------
# Helpers


def _ok(request: httpx.Request) -> httpx.Response:  # noqa: U100 - MockTransport passes it; no use for it here.
  """Answer any request with an empty JSON object.

  Returns:
      An empty JSON 200 response.
  """
  return httpx.Response(200, json={})


def _refuse(request: httpx.Request) -> httpx.Response:
  """Fail any request the way a refused connection does.

  Args:
      request: The request being refused.

  Raises:
      ConnectError: Always.
  """
  raise httpx.ConnectError("Connection failed", request=request)


def _recording_client(
  status: int = 200,
  json_body: Any = None,
  text_body: Optional[str] = None,
  content_type: Optional[str] = None,
  **kwargs: Any,
) -> Tuple[ApiClient, List[httpx.Request]]:
  """Build an ApiClient whose transport records each request and answers it.

  Args:
      status: Status code of every response.
      json_body: JSON response body; used when ``text_body`` is None.
      text_body: Raw response body.
      content_type: Response Content-Type; overrides the one httpx sets.
      kwargs: Passed through to ApiClient.

  Returns:
      The client and the list each request is appended to.
  """
  seen: List[httpx.Request] = []

  def handler(request: httpx.Request) -> httpx.Response:
    seen.append(request)
    headers = {"Content-Type": content_type} if content_type else None

    if text_body is not None:
      return httpx.Response(status, text=text_body, headers=headers)

    return httpx.Response(status, json=json_body, headers=headers)

  return ApiClient(transport=httpx.MockTransport(handler), **kwargs), seen


class _UnixHTTPServer(socketserver.UnixStreamServer):
  """HTTP server on a Unix socket, standing in for bw serve."""


class _EchoHostHandler(http.server.BaseHTTPRequestHandler):
  """Answer every GET with the Host header and path it arrived with."""

  def do_GET(self: "_EchoHostHandler") -> None:  # noqa: N802 - BaseHTTPRequestHandler's dispatch name.
    """Echo the Host header and path as JSON."""
    body = json.dumps({"host": self.headers["Host"], "path": self.path}).encode()
    self.send_response(200)
    self.send_header("Content-Type", "application/json")
    self.send_header("Content-Length", str(len(body)))
    self.end_headers()
    self.wfile.write(body)

  def log_message(self: "_EchoHostHandler", *args: Any) -> None:  # noqa: U100 - overridden only to discard them.
    """Keep the test output quiet; the default logs every request to stderr.

    Args:
        args: The format string and its arguments, ignored.
    """
