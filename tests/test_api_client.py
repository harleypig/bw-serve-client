"""Tests for ApiClient module."""

import json
from unittest.mock import Mock
from unittest.mock import patch

import pytest
import requests

from bw_serve_client.api_client import ApiClient
from bw_serve_client.api_client import AuthenticationError
from bw_serve_client.api_client import BitwardenAPIError
from bw_serve_client.api_client import NotFoundError
from bw_serve_client.api_client import ServerError
from bw_serve_client.api_client import ValidationError


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

  def test_handle_error_success(self: "TestApiClient") -> None:
    """Test error handling for successful responses."""
    client = ApiClient()
    response = Mock()
    response.status_code = 200

    client._handle_error(response)  # act

  def test_handle_error_401(self: "TestApiClient") -> None:
    """Test error handling for 401 Unauthorized."""
    client = ApiClient()
    response = Mock()
    response.status_code = 401
    response.json.return_value = {"message": "Unauthorized"}

    with pytest.raises(AuthenticationError, match="Unauthorized"):  # act
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

    with pytest.raises(NotFoundError, match="Not Found"):  # act
      client._handle_error(response)

  def test_handle_error_500(self: "TestApiClient") -> None:
    """Test error handling for 500 Server Error."""
    client = ApiClient()
    response = Mock()
    response.status_code = 500
    response.json.return_value = {"message": "Server Error"}

    with pytest.raises(ServerError, match="Server Error"):  # act
      client._handle_error(response)

  @patch('bw_serve_client.api_client.requests.Session')
  def test_get_request(self: "TestApiClient", mock_session_class: Mock) -> None:
    """Test GET request method."""
    mock_session = Mock()
    mock_session.headers = {"Content-Type": "application/json", "Accept": "application/json"}
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = {"data": "test"}
    mock_session.request.return_value = mock_response
    mock_session_class.return_value = mock_session
    client = ApiClient()
    client.session = mock_session

    result = client.get("/test", params={"key": "value"})  # act

    mock_session.request.assert_called_once_with(
      method='GET',
      url='http://localhost:8087/test',
      json=None,
      data=None,
      files=None,
      params={"key": "value"},
      headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "bw-serve-client/0.1.1"
      },
      timeout=30
    )
    assert result == {"data": "test"}

  @patch('bw_serve_client.api_client.requests.Session')
  def test_post_request(self: "TestApiClient", mock_session_class: Mock) -> None:
    """Test POST request method."""
    mock_session = Mock()
    mock_session.headers = {"Content-Type": "application/json", "Accept": "application/json"}
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = {"created": True}
    mock_session.request.return_value = mock_response
    mock_session_class.return_value = mock_session
    client = ApiClient()
    client.session = mock_session
    data = {"name": "test"}

    result = client.post("/test", data=data)  # act

    # Data should be serialized by _serialize_data
    mock_session.request.assert_called_once_with(
      method='POST',
      url='http://localhost:8087/test',
      json=data,
      data=None,
      files=None,
      params=None,
      headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "bw-serve-client/0.1.1"
      },
      timeout=30
    )
    assert result == {"created": True}

  @patch('bw_serve_client.api_client.requests.Session')
  def test_post_request_with_files(self: "TestApiClient", mock_session_class: Mock) -> None:
    """Test POST request method with file upload."""
    mock_session = Mock()
    mock_session.headers = {"Content-Type": "application/json", "Accept": "application/json"}
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = {"uploaded": True}
    mock_session.request.return_value = mock_response
    mock_session_class.return_value = mock_session
    client = ApiClient()
    client.session = mock_session
    data = {"name": "test"}
    files = {"file": "content"}

    result = client.post("/test", data=data, files=files)  # act

    mock_session.request.assert_called_once_with(
      method='POST',
      url='http://localhost:8087/test',
      json=None,
      data=data,
      files=files,
      params=None,
      headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "bw-serve-client/0.1.1"
      },
      timeout=30
    )
    assert result == {"uploaded": True}

  def test_context_manager(self: "TestApiClient") -> None:  # noqa: AAA01
    """Test context manager functionality."""
    with patch('bw_serve_client.api_client.requests.Session') as mock_session_class:
      mock_session = Mock()
      mock_session_class.return_value = mock_session
      with ApiClient() as client:  # act
        assert client.session == mock_session
      mock_session.close.assert_called_once()

  def test_close(self: "TestApiClient") -> None:
    """Test close method."""
    with patch('bw_serve_client.api_client.requests.Session') as mock_session_class:
      mock_session = Mock()
      mock_session_class.return_value = mock_session
      client = ApiClient()

      client.close()  # act

      mock_session.close.assert_called_once()

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

    with pytest.raises(BitwardenAPIError, match="I'm a teapot"):  # act
      client._handle_error(response)

  @patch('bw_serve_client.api_client.requests.Session')
  def test_make_request_with_headers(self: "TestApiClient", mock_session_class: Mock) -> None:
    """Test _make_request with custom headers."""
    mock_session = Mock()
    mock_session.headers = {"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "bw-serve-client/1.0.0"}
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = {"data": "test"}
    mock_session.request.return_value = mock_response
    mock_session_class.return_value = mock_session
    client = ApiClient()
    client.session = mock_session
    custom_headers = {"Authorization": "Bearer token"}

    client._make_request("GET", "/test", headers=custom_headers)  # act

    # Check that custom headers were merged with session headers
    expected_headers = {
      "Content-Type": "application/json",
      "Accept": "application/json",
      "User-Agent": "bw-serve-client/0.1.1",
      "Authorization": "Bearer token"
    }
    mock_session.request.assert_called_once()
    call_args = mock_session.request.call_args
    assert call_args[1]["headers"] == expected_headers

  @patch('bw_serve_client.api_client.requests.Session')
  def test_make_request_exception(self: "TestApiClient", mock_session_class: Mock) -> None:
    """Test _make_request with RequestException."""
    mock_session = Mock()
    mock_session.headers = {"Content-Type": "application/json"}
    mock_session.request.side_effect = requests.exceptions.RequestException("Connection failed")
    mock_session_class.return_value = mock_session
    client = ApiClient()
    client.session = mock_session

    with pytest.raises(BitwardenAPIError, match="Request failed: Connection failed"):  # act
      client._make_request("GET", "/test")

  @patch('bw_serve_client.api_client.requests.Session')
  def test_put_request(self: "TestApiClient", mock_session_class: Mock) -> None:
    """Test PUT request method."""
    mock_session = Mock()
    mock_session.headers = {"Content-Type": "application/json", "Accept": "application/json"}
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = {"updated": True}
    mock_session.request.return_value = mock_response
    mock_session_class.return_value = mock_session
    client = ApiClient()
    client.session = mock_session
    data = {"name": "updated"}

    result = client.put("/test", data=data)  # act

    mock_session.request.assert_called_once_with(
      method='PUT',
      url='http://localhost:8087/test',
      json=data,
      data=None,
      files=None,
      params=None,
      headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "bw-serve-client/0.1.1"
      },
      timeout=30
    )
    assert result == {"updated": True}

  @patch('bw_serve_client.api_client.requests.Session')
  def test_delete_request(self: "TestApiClient", mock_session_class: Mock) -> None:
    """Test DELETE request method."""
    mock_session = Mock()
    mock_session.headers = {"Content-Type": "application/json", "Accept": "application/json"}
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = {"deleted": True}
    mock_session.request.return_value = mock_response
    mock_session_class.return_value = mock_session
    client = ApiClient()
    client.session = mock_session

    result = client.delete("/test")  # act

    mock_session.request.assert_called_once_with(
      method='DELETE',
      url='http://localhost:8087/test',
      json=None,
      data=None,
      files=None,
      params=None,
      headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "bw-serve-client/0.1.1"
      },
      timeout=30
    )
    assert result == {"deleted": True}

  @patch('bw_serve_client.api_client.requests.Session')
  def test_serialization_integration_post(self: "TestApiClient", mock_session_class: Mock) -> None:
    """Test serialization integration with POST request."""
    mock_session = Mock()
    mock_session.headers = {"Content-Type": "application/json"}
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = {"created": True}
    mock_session.request.return_value = mock_response
    mock_session_class.return_value = mock_session
    client = ApiClient()
    client.session = mock_session

    # Test with complex nested data
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

    # Verify the data was passed as JSON (not serialized again)
    mock_session.request.assert_called_once()
    call_args = mock_session.request.call_args
    assert call_args[1]["json"] == complex_data
    assert result == {"created": True}

  @patch('bw_serve_client.api_client.requests.Session')
  def test_deserialization_integration_get(self: "TestApiClient", mock_session_class: Mock) -> None:
    """Test deserialization integration with GET request."""
    mock_session = Mock()
    mock_session.headers = {"Content-Type": "application/json"}
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json; charset=utf-8"}

    # Test with complex nested response
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
    mock_response.json.return_value = complex_response
    mock_session.request.return_value = mock_response
    mock_session_class.return_value = mock_session
    client = ApiClient()
    client.session = mock_session

    result = client.get("/items")  # act

    assert result == complex_response
    assert len(result["data"]) == 2
    assert result["data"][0]["name"] == "Item 1"
    assert result["pagination"]["total"] == 2

  @patch('bw_serve_client.api_client.requests.Session')
  def test_serialization_string_data_post(self: "TestApiClient", mock_session_class: Mock) -> None:
    """Test serialization with string data in POST request."""
    mock_session = Mock()
    mock_session.headers = {"Content-Type": "application/json"}
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = {"processed": True}
    mock_session.request.return_value = mock_response
    mock_session_class.return_value = mock_session
    client = ApiClient()
    client.session = mock_session

    # Test with JSON string data
    json_string = '{"name": "test", "value": 123}'

    result = client.post("/process", data=json_string)  # act

    # The string should be parsed by _serialize_data and converted to dict
    mock_session.request.assert_called_once()
    call_args = mock_session.request.call_args
    expected_data = {"name": "test", "value": 123}
    assert call_args[1]["json"] == expected_data
    assert result == {"processed": True}

  @patch('bw_serve_client.api_client.requests.Session')
  def test_deserialization_error_fallback(self: "TestApiClient", mock_session_class: Mock) -> None:
    """Test deserialization error fallback to text."""
    mock_session = Mock()
    mock_session.headers = {"Content-Type": "application/json"}
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
    mock_response.text = "Invalid JSON response"
    mock_session.request.return_value = mock_response
    mock_session_class.return_value = mock_session
    client = ApiClient()
    client.session = mock_session

    result = client.get("/test")  # act

    # Should fallback to text when JSON parsing fails
    assert result == "Invalid JSON response"

  @patch('bw_serve_client.api_client.ApiClient._serialize_data')
  @patch('bw_serve_client.api_client.requests.Session')
  def test_serialize_data_called_in_post(self: "TestApiClient", mock_session_class: Mock, mock_serialize: Mock) -> None:
    """Test that _serialize_data is called during POST requests."""
    mock_session = Mock()
    mock_session.headers = {"Content-Type": "application/json"}
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = {"created": True}
    mock_session.request.return_value = mock_response
    mock_session_class.return_value = mock_session

    # Mock _serialize_data to return the data as-is
    mock_serialize.return_value = {"name": "test"}
    client = ApiClient()
    client.session = mock_session
    data = {"name": "test"}

    client.post("/test", data=data)  # act

    # Verify _serialize_data was called with correct parameters
    mock_serialize.assert_called_once_with(data, "application/json")

  @patch('bw_serve_client.api_client.ApiClient._serialize_data')
  @patch('bw_serve_client.api_client.requests.Session')
  def test_serialize_data_called_in_put(self: "TestApiClient", mock_session_class: Mock, mock_serialize: Mock) -> None:
    """Test that _serialize_data is called during PUT requests."""
    mock_session = Mock()
    mock_session.headers = {"Content-Type": "application/json"}
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = {"updated": True}
    mock_session.request.return_value = mock_response
    mock_session_class.return_value = mock_session

    # Mock _serialize_data to return the data as-is
    mock_serialize.return_value = {"name": "updated"}
    client = ApiClient()
    client.session = mock_session
    data = {"name": "updated"}

    client.put("/test", data=data)  # act

    # Verify _serialize_data was called with correct parameters
    mock_serialize.assert_called_once_with(data, "application/json")

  @patch('bw_serve_client.api_client.ApiClient._serialize_data')
  @patch('bw_serve_client.api_client.requests.Session')
  def test_serialize_data_with_custom_content_type(self: "TestApiClient", mock_session_class: Mock, mock_serialize: Mock) -> None:
    """Test that _serialize_data is called with custom content type."""
    mock_session = Mock()
    mock_session.headers = {"Content-Type": "text/plain"}
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "text/plain"}
    mock_response.text = "Success"
    mock_session.request.return_value = mock_response
    mock_session_class.return_value = mock_session

    # Mock _serialize_data to return string representation
    mock_serialize.return_value = "test data"
    client = ApiClient()
    client.session = mock_session
    data = {"name": "test"}

    client._make_request("POST", "/test", data=data, headers={"Content-Type": "text/plain"})  # act

    # Verify _serialize_data was called with custom content type
    mock_serialize.assert_called_once_with(data, "text/plain")

  def test_make_request_unsupported_method(self: "TestApiClient") -> None:
    """Test that _make_request raises error for unsupported HTTP methods."""
    client = ApiClient()

    with pytest.raises(BitwardenAPIError) as exc_info:  # act
      client._make_request("PATCH", "/test")

    assert "Unsupported HTTP method: PATCH" in str(exc_info.value)
    assert "Supported methods are: DELETE, GET, POST, PUT" in str(exc_info.value)

  def test_make_request_case_insensitive_method(self: "TestApiClient") -> None:
    """Test that _make_request accepts case-insensitive HTTP methods."""
    with patch('bw_serve_client.api_client.requests.Session') as mock_session_class:
      mock_session = Mock()
      mock_session.headers = {}  # Add proper headers attribute
      mock_response = Mock()
      mock_response.status_code = 200
      mock_response.headers = {"content-type": "application/json"}
      mock_response.json.return_value = {"success": True}
      mock_session.request.return_value = mock_response
      mock_session_class.return_value = mock_session
      client = ApiClient()
      client.session = mock_session

      result = client._make_request("get", "/test")  # act

      assert result == mock_response

      # Verify the method was converted to uppercase
      call_args = mock_session.request.call_args
      assert call_args[1]["method"] == "GET"  # Method should be uppercase
      assert call_args[1]["url"] == "http://localhost:8087/test"
