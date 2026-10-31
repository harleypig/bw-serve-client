"""ApiClient - Base HTTP communication layer for Bitwarden Vault Management API.

This module provides the core HTTP communication functionality for interacting
with the Bitwarden Vault Management API via the 'bw serve' command.
"""

import json
import logging
from typing import Any, Dict, Optional, Union
from urllib.parse import urljoin

import httpx

# Type aliases for complex types
RequestData = Optional[Union[Dict[str, Any], str]]
QueryParams = Optional[Dict[str, Any]]

UNIX_SCHEME = "unix://"


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

  The client connects to a running ``bw serve``; it never starts or stops
  it. It reaches the server one of three ways:

  - **URL** (the default): built from ``protocol``, ``domain``, ``port``
    and ``path``, or given whole as ``base_url``.
  - **Unix socket**: ``base_url="unix:///path/to/bw.sock"``, joined with
    ``path``. Requests go over the socket with ``Host: localhost:<port>``,
    so ``port`` must match the port ``bw serve`` was started with.
  - **Caller's transport**: any ``httpx.BaseTransport`` as ``transport``,
    used as-is, so ``max_retries`` does not apply to it.

  ``max_retries`` retries failed connection attempts only; an HTTP error
  status is never retried.

  Args:
      protocol: Protocol to use (http, https) - default: http
      domain: Domain or IP address - default: localhost
      port: Port number - default: 8087
      path: Base path - default: empty string
      timeout: Request timeout in seconds
      max_retries: Connection attempts to retry
      user_agent: Custom User-Agent string (default: 'bw-serve-client/<version>')
      logger: Optional logger instance for logging requests/responses
      base_url: Full base URL, or ``unix://<socket path>``; replaces the URL parts
      transport: Caller-supplied httpx transport

  Raises:
      ValueError: If a ``unix://`` base_url has no path or comes with a transport.

  Attributes:
      session: The underlying ``httpx.Client`` for HTTP communication
  """

  session: httpx.Client

  # ---------------------------------------------------------------------------
  # for use with 'with'

  def __enter__(self: "ApiClient") -> "ApiClient":
    """Context manager entry.

    Returns:
        ApiClient: The instance itself for context management.
    """
    return self

  def __exit__(self: "ApiClient", _exc_type: Any, _exc_val: Any, _exc_tb: Any) -> None:
    """Context manager exit."""
    self.close()

  def close(self: "ApiClient") -> None:
    """Close the session and clean up resources."""
    self.session.close()

  # ---------------------------------------------------------------------------
  # Class methods

  def __init__(
    self: "ApiClient",
    protocol: str = "http",
    domain: str = "localhost",
    port: int = 8087,
    path: str = "",
    timeout: int = 30,
    max_retries: int = 3,
    user_agent: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
    *,
    base_url: Optional[str] = None,
    transport: Optional[httpx.BaseTransport] = None
  ) -> None:
    from . import __version__

    headers = {'Accept': 'application/json', 'User-Agent': user_agent or f'bw-serve-client/{__version__}'}

    if base_url is not None and base_url.startswith(UNIX_SCHEME):
      if transport is not None:
        raise ValueError("pass either a unix:// base_url or a transport, not both")

      socket_path = base_url[len(UNIX_SCHEME):]

      if not socket_path:
        raise ValueError(f"no socket path in base_url {base_url!r}")

      transport = httpx.HTTPTransport(uds=socket_path, retries=max_retries)
      base_url = f"http://localhost:{port}{path}"

      # bw CLI 2026.6.0+ 403s any other Host (bitwarden/clients#22867).
      headers['Host'] = f"localhost:{port}"

    elif base_url is None:
      base_url = f"{protocol}://{domain}:{port}{path}"

    if transport is None:
      transport = httpx.HTTPTransport(retries=max_retries)

    self.base_url = base_url.rstrip('/')
    self.timeout = timeout
    self.logger = logger or self._setup_default_logger()

    # No default Content-Type: httpx sets it per body (JSON, multipart
    # with its boundary), and a client default would override that.
    self.session = httpx.Client(transport=transport, headers=headers, timeout=timeout)

  def _setup_default_logger(self: "ApiClient") -> logging.Logger:
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
    self: "ApiClient",
    method: str,
    endpoint: str,
    data: RequestData = None,
    params: QueryParams = None,
    files: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None
  ) -> httpx.Response:
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

    # Log request
    self.logger.debug(f"Making {method} request to {url}")

    if params:
      self.logger.debug(f"Query parameters: {params}")

    if data and not files:
      self.logger.debug(f"Request data: {data}")

    content_type = httpx.Headers(headers).get('Content-Type', 'application/json')
    use_json = not files and content_type.startswith('application/json')

    # httpx takes a JSON body, raw text and form fields as three separate
    # arguments.
    body: Dict[str, Any] = {}

    if data is not None:
      serialized_data = self._serialize_data(data, content_type)

      if use_json:
        body['json'] = serialized_data

      elif isinstance(serialized_data, (str, bytes)):
        body['content'] = serialized_data

      else:
        body['data'] = serialized_data

    try:
      response = self.session.request(method=method, url=url, files=files, params=params, headers=headers, **body)

      # Log response
      self.logger.debug(f"Response status: {response.status_code}")
      self.logger.debug(f"Response headers: {dict(response.headers)}")

      # Handle errors
      self._handle_error(response)

      return response

    except httpx.RequestError as e:
      self.logger.exception("Request failed")
      raise BitwardenAPIError(f"Request failed: {e}") from e

  def _serialize_data(self: "ApiClient", data: Any, content_type: str = "application/json") -> Any:
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

  def _deserialize_data(self: "ApiClient", response: httpx.Response) -> Any:
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

  def _handle_error(self: "ApiClient", response: httpx.Response) -> None:
    """Handle HTTP errors and raise appropriate exceptions.

    Args:
        response: Response object to check for errors

    Raises:
        AuthenticationError: When status code is 401 (Unauthorized).
        ValidationError: When status code is 400 (Bad Request).
        NotFoundError: When status code is 404 (Not Found).
        ServerError: When status code is 500 or higher (Server Error).
        BitwardenAPIError: For any other error status codes.
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

  def _make_request_and_deserialize(self: "ApiClient", method: str, endpoint: str, **kwargs: Any) -> Any:
    r"""Make a request and deserialize the response.

    Args:
        method: HTTP method
        endpoint: API endpoint
        kwargs: Additional arguments for _make_request

    Returns:
        Deserialized response data
    """
    response = self._make_request(method, endpoint, **kwargs)
    return self._deserialize_data(response)

  def get(self: "ApiClient", endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Make a GET request.

    Args:
        endpoint: API endpoint
        params: Query parameters

    Returns:
        Deserialized response data
    """
    return self._make_request_and_deserialize('GET', endpoint, params=params)

  def post(self: "ApiClient", endpoint: str, data: RequestData = None, files: Optional[Dict[str, Any]] = None) -> Any:
    """Make a POST request.

    Args:
        endpoint: API endpoint
        data: Request body data
        files: Files to upload

    Returns:
        Deserialized response data
    """
    return self._make_request_and_deserialize('POST', endpoint, data=data, files=files)

  def put(self: "ApiClient", endpoint: str, data: RequestData = None) -> Any:
    """Make a PUT request.

    Args:
        endpoint: API endpoint
        data: Request body data

    Returns:
        Deserialized response data
    """
    return self._make_request_and_deserialize('PUT', endpoint, data=data)

  def delete(self: "ApiClient", endpoint: str) -> Any:
    """Make a DELETE request.

    Args:
        endpoint: API endpoint

    Returns:
        Deserialized response data
    """
    return self._make_request_and_deserialize('DELETE', endpoint)
