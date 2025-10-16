"""ApiClient - Base HTTP communication layer for Bitwarden Vault Management API.

This module provides the core HTTP communication functionality for interacting
with the Bitwarden Vault Management API via the 'bw serve' command.
"""

import json
import logging
from typing import Any, Dict, Optional, Union
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class BitwardenAPIError(Exception):
  """Base exception for Bitwarden API errors."""

  pass


class AuthenticationError(BitwardenAPIError):
  """Raised when authentication fails."""

  pass


class ValidationError(BitwardenAPIError):
  """Raised when request validation fails."""

  pass


class NotFoundError(BitwardenAPIError):
  """Raised when a resource is not found."""

  pass


class ServerError(BitwardenAPIError):
  """Raised when the server returns an error."""

  pass


class ApiClient:
  """Base HTTP client for Bitwarden Vault Management API communication.

  Handles all HTTP requests, response processing, error handling, and
  data serialization/deserialization for the Bitwarden API.
  """

  # ---------------------------------------------------------------------------
  # for use with 'with'

  def __enter__(self):
    """Context manager entry."""
    return self

  def __exit__(self, _exc_type, _exc_val, _exc_tb):
    """Context manager exit."""
    self.close()

  def close(self) -> None:
    """Close the session and clean up resources."""
    self.session.close()

  # ---------------------------------------------------------------------------
  # Class methods

  def __init__(
    self,
    protocol: str = "http",
    domain: str = "localhost",
    port: int = 8087,
    path: str = "",
    timeout: int = 30,
    max_retries: int = 3,
    user_agent: Optional[str] = None,
    logger: Optional[logging.Logger] = None
  ):
    """Initialize the API client.

    Args:
        protocol: Protocol to use (http, https) - default: http
        domain: Domain or IP address - default: localhost
        port: Port number - default: 8087
        path: Base path - default: empty string
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        user_agent: Custom User-Agent string (default: 'bw-serve-client/0.1.0')
        logger: Optional logger instance for logging requests/responses
    """
    # Build base_url from components
    self.base_url = f"{protocol}://{domain}:{port}{path}".rstrip('/')

    self.timeout = timeout
    self.logger = logger or self._setup_default_logger()

    # Setup session with retry strategy
    self.session = requests.Session()

    retry_strategy = Retry(
      total=max_retries,
      backoff_factor=1,
      status_forcelist=[429, 500, 502, 503, 504],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    self.session.mount("http://", adapter)
    self.session.mount("https://", adapter)

    # Set default headers
    from . import __version__
    self.session.headers.update({
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'User-Agent': user_agent or f'bw-serve-client/{__version__}'
    })

  def _setup_default_logger(self) -> logging.Logger:
    """Set up default logger for the API client."""
    logger = logging.getLogger(__name__)
    if not logger.handlers:
      handler = logging.StreamHandler()
      formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
      handler.setFormatter(formatter)
      logger.addHandler(handler)
      logger.setLevel(logging.INFO)
    return logger

  def _make_request(
    self,
    method: str,
    endpoint: str,
    data: Optional[Union[Dict[str, Any], str]] = None,
    params: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None
  ) -> requests.Response:
    """Make an HTTP request to the API.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE). Must be one of the
            supported methods or BitwardenAPIError will be raised.
        endpoint: API endpoint path
        data: Request body data
        params: Query parameters
        files: Files to upload (for multipart requests)
        headers: Additional headers

    Returns:
        Response object

    Raises:
        BitwardenAPIError: For various API errors, including unsupported
            HTTP methods
    """
    # Validate HTTP method
    supported_methods = {'GET', 'POST', 'PUT', 'DELETE'}
    method_upper = method.upper()
    if method_upper not in supported_methods:
      raise BitwardenAPIError(
        f"Unsupported HTTP method: {method}. "
        f"Supported methods are: {', '.join(sorted(supported_methods))}"
      )

    # Use uppercase method for the actual request
    method = method_upper

    url = urljoin(self.base_url, endpoint.lstrip('/'))

    # Prepare headers
    request_headers = dict(self.session.headers)

    if headers:
      request_headers.update(headers)

    # Log request
    self.logger.debug(f"Making {method} request to {url}")

    if params:
      self.logger.debug(f"Query parameters: {params}")

    if data and not files:
      self.logger.debug(f"Request data: {data}")

    try:
      # Serialize data based on content type
      serialized_data = None
      if data is not None:
        content_type = str(request_headers.get('Content-Type', 'application/json'))
        serialized_data = self._serialize_data(data, content_type)

      # Determine whether to use json or data parameter based on content type
      content_type_str = str(request_headers.get('Content-Type', 'application/json'))
      use_json = (not files and content_type_str.startswith('application/json'))

      response = self.session.request(
        method=method,
        url=url,
        json=serialized_data if use_json else None,
        data=serialized_data if not use_json else None,
        files=files,
        params=params,
        headers=request_headers,
        timeout=self.timeout
      )

      # Log response
      self.logger.debug(f"Response status: {response.status_code}")
      self.logger.debug(f"Response headers: {dict(response.headers)}")

      # Handle errors
      self._handle_error(response)

      return response

    except requests.exceptions.RequestException as e:
      self.logger.error(f"Request failed: {e}")
      raise BitwardenAPIError(f"Request failed: {e}") from e

  def _serialize_data(self,
                      data: Any,
                      content_type: str = "application/json") -> Union[Dict[str, Any], str]:
    """Serialize data for API requests.

    Args:
        data: Data to serialize
        content_type: Content type for serialization

    Returns:
        Serialized data
    """
    if content_type == "application/json":
      if isinstance(data, str):
        try:
          return json.loads(data)

        except json.JSONDecodeError:
          return data

      return data

    elif content_type == "multipart/form-data":
      return data

    else:
      return str(data)

  def _deserialize_data(self, response: requests.Response) -> Any:
    """Deserialize API response data.

    Args:
        response: Response object to deserialize

    Returns:
        Deserialized data
    """
    content_type = response.headers.get('content-type', '').lower()

    if 'application/json' in content_type:
      try:
        return response.json()

      except json.JSONDecodeError as e:
        self.logger.warning(f"Failed to parse JSON response: {e}")
        return response.text

    else:
      return response.text

  def _handle_error(self, response: requests.Response) -> None:
    """Handle HTTP errors and raise appropriate exceptions.

    Args:
        response: Response object to check for errors

    Raises:
        Various BitwardenAPIError subclasses based on status code
    """
    if response.status_code < 400:
      return

    error_message = f"API request failed with status {response.status_code}"

    try:
      error_data = response.json()

      if isinstance(error_data, dict) and 'message' in error_data:
        error_message = error_data['message']

    except (json.JSONDecodeError, KeyError):
      error_message = response.text or error_message

    self.logger.error(f"{error_message} (Status: {response.status_code})")

    if response.status_code == 401:
      raise AuthenticationError(error_message)

    elif response.status_code == 400:
      raise ValidationError(error_message)

    elif response.status_code == 404:
      raise NotFoundError(error_message)

    elif response.status_code >= 500:
      raise ServerError(error_message)

    else:
      raise BitwardenAPIError(error_message)

  # ---------------------------------------------------------------------------
  # Public methods

  def _make_request_and_deserialize(self, method: str, endpoint: str, **kwargs) -> Any:
    """Make a request and deserialize the response.

    Args:
        method: HTTP method
        endpoint: API endpoint
        **kwargs: Additional arguments for _make_request

    Returns:
        Deserialized response data
    """
    response = self._make_request(method, endpoint, **kwargs)
    return self._deserialize_data(response)

  def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Make a GET request.

    Args:
        endpoint: API endpoint
        params: Query parameters

    Returns:
        Deserialized response data
    """
    return self._make_request_and_deserialize('GET', endpoint, params=params)

  def post(
    self,
    endpoint: str,
    data: Optional[Union[Dict[str, Any], str]] = None,
    files: Optional[Dict[str, Any]] = None
  ) -> Any:
    """Make a POST request.

    Args:
        endpoint: API endpoint
        data: Request body data
        files: Files to upload

    Returns:
        Deserialized response data
    """
    return self._make_request_and_deserialize('POST', endpoint, data=data, files=files)

  def put(self, endpoint: str, data: Optional[Union[Dict[str, Any], str]] = None) -> Any:
    """Make a PUT request.

    Args:
        endpoint: API endpoint
        data: Request body data

    Returns:
        Deserialized response data
    """
    return self._make_request_and_deserialize('PUT', endpoint, data=data)

  def delete(self, endpoint: str) -> Any:
    """Make a DELETE request.

    Args:
        endpoint: API endpoint

    Returns:
        Deserialized response data
    """
    return self._make_request_and_deserialize('DELETE', endpoint)
