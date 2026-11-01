"""ApiClient - Base HTTP communication layer for Bitwarden Vault Management API.

This module provides the core HTTP communication functionality for interacting
with the Bitwarden Vault Management API via the 'bw serve' command.
"""

import json
import logging
from typing import Any, Dict, Optional, Union

import httpx

from .errors import category_for_status
from .errors import DefaultErrorHandler
from .errors import ErrorHandler
from .errors import ExternalServiceError
from .errors import InternalError
from .errors import ValidationError

# Type aliases for complex types
RequestData = Optional[Union[Dict[str, Any], str]]
QueryParams = Optional[Dict[str, Any]]

UNIX_SCHEME = "unix://"


# -----------------------------------------------------------------------------
def _media_type(content_type: str) -> str:
  """Reduce a Content-Type header value to its media type.

  Args:
      content_type: A header value such as ``application/json; charset=utf-8``.

  Returns:
      The media type, lower case, without parameters.
  """
  return content_type.split(';', 1)[0].strip().lower()


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

  Every failure -- an error status, a failed connection, a timeout -- goes
  to ``error_handler``, whose return value comes back in place of the
  response when it does not raise. The default handler raises, and logs to
  ``logger``; the default logger is the module's, with no handler or level
  set, so where its records go is the application's choice.

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
      error_handler: Where failures go; a :class:`DefaultErrorHandler` by default

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
    transport: Optional[httpx.BaseTransport] = None,
    error_handler: Optional[ErrorHandler] = None
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
    self.logger = logger if logger is not None else logging.getLogger(__name__)
    self.error_handler = error_handler if error_handler is not None else DefaultErrorHandler(logger=self.logger)

    # No default Content-Type: httpx sets it per body (JSON, multipart
    # with its boundary), and a client default would override that.
    self.session = httpx.Client(transport=transport, headers=headers, timeout=timeout)

  def _make_request(
    self: "ApiClient",
    method: str,
    endpoint: str,
    data: RequestData = None,
    params: QueryParams = None,
    files: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    *,
    error_handler: Optional[ErrorHandler] = None
  ) -> Union[httpx.Response, Any]:
    """Make an HTTP request to the API.

    A failure goes to ``error_handler``, or to the client's handler when
    that is ``None``: an unsupported method as an ``InternalError``, a URL
    httpx cannot build as a ``ValidationError``, a transport failure as an
    ``ExternalServiceError``, and an error status as the category
    ``category_for_status()`` picks.

    Query parameters whose value is ``None`` are left out.

    Args:
        method: HTTP method: GET, POST, PUT or DELETE, in any case.
        endpoint: API endpoint path
        data: Request body data
        params: Query parameters
        files: Files to upload (for multipart requests)
        headers: Additional headers
        error_handler: Handler for this request's failures.

    Returns:
        The response, or the handler's return value when it does not raise.
    """
    handler = error_handler if error_handler is not None else self.error_handler

    supported_methods = {'GET', 'POST', 'PUT', 'DELETE'}
    method_upper = method.upper()

    if method_upper not in supported_methods:
      return handler.handle(
        InternalError, f"Unsupported HTTP method: {method}. "
        f"Supported methods are: {', '.join(sorted(supported_methods))}"
      )

    # Use uppercase method for the actual request
    method = method_upper

    # Not urljoin: base_url has no trailing slash, so urljoin would drop
    # its last path segment.
    url = f"{self.base_url}/{endpoint.lstrip('/')}"

    params = {key: value for key, value in (params or {}).items() if value is not None} or None

    # Log request
    self.logger.debug(f"Making {method} request to {url}")

    if params:
      self.logger.debug(f"Query parameters: {params}")

    # Field names only: a body can carry the master password or vault
    # secrets, and a debug log is no place for either.
    if isinstance(data, dict) and not files:
      self.logger.debug(f"Request fields: {sorted(data)}")

    content_type = httpx.Headers(headers).get('Content-Type', 'application/json')
    use_json = not files and _media_type(content_type) == 'application/json'

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

    response = self._send(method, url, files=files, params=params, headers=headers, **body)

    if isinstance(response, httpx.InvalidURL):
      return handler.handle(ValidationError, f"Invalid URL: {response}", cause=response)

    if isinstance(response, httpx.RequestError):
      return handler.handle(ExternalServiceError, f"Request failed: {response}", cause=response)

    # Log response
    self.logger.debug(f"Response status: {response.status_code}")
    self.logger.debug(f"Response headers: {dict(response.headers)}")

    if response.status_code >= 400:
      return self._handle_error(response, handler)

    return response

  def _send(self: "ApiClient", method: str, url: str, **kwargs: Any) -> Union[httpx.Response, httpx.RequestError, httpx.InvalidURL]:
    """Send one request, returning a failure rather than raising it.

    A transport failure, or a URL httpx cannot build, comes back as a copy
    of httpx's error without its request, which holds the body -- the
    master password, on ``/unlock``. Returning it, rather than handling it
    in the ``except`` block, keeps the original from becoming the
    ``__context__`` of whatever the error handler raises.

    Args:
        method: HTTP method, upper case.
        url: Full request URL.
        kwargs: Further arguments for ``httpx.Client.request``.

    Returns:
        The response, or the failure.
    """
    try:
      return self.session.request(method=method, url=url, **kwargs)

    except (httpx.RequestError, httpx.InvalidURL) as e:
      failure = type(e)(str(e))
      failure.__cause__ = e.__cause__
      return failure

  def _serialize_data(self: "ApiClient", data: Any, content_type: str = "application/json") -> Any:
    """Serialize data for API requests.

    Args:
        data: Data to serialize
        content_type: Content type for serialization

    Returns:
        Serialized data
    """
    media_type = _media_type(content_type)

    if media_type == "application/json":
      if isinstance(data, str):
        try:
          return json.loads(data)

        except json.JSONDecodeError:
          return data

      return data

    elif media_type == "multipart/form-data":
      return data

    else:
      return str(data)

  def _deserialize_data(self: "ApiClient", response: httpx.Response) -> Any:
    """Deserialize API response data.

    Args:
        response: Response object to deserialize

    Returns:
        The parsed JSON for a JSON response, the raw ``bytes`` for an
        ``application/octet-stream`` one (a downloaded file), and the
        text for anything else.
    """
    content_type = response.headers.get('content-type', '').lower()

    if 'application/json' in content_type:
      try:
        return response.json()

      except json.JSONDecodeError as e:
        self.logger.warning(f"Failed to parse JSON response: {e}")
        return response.text

    elif _media_type(content_type) == 'application/octet-stream':
      return response.content

    else:
      return response.text

  def _handle_error(self: "ApiClient", response: httpx.Response, handler: ErrorHandler) -> Any:
    """Pass an error response to the error handler.

    Args:
        response: A response whose status is 400 or above.
        handler: The handler the failure goes to.

    Returns:
        Whatever the handler returns, when it does not raise.
    """
    error_message = f"API request failed with status {response.status_code}"

    try:
      error_data = response.json()

      if isinstance(error_data, dict) and isinstance(error_data.get('message'), str):
        error_message = error_data['message']

    except (json.JSONDecodeError, UnicodeDecodeError, KeyError):
      error_message = response.text or error_message

    category = category_for_status(response.status_code, error_message)

    return handler.handle(category, error_message, status_code=response.status_code)

  # ---------------------------------------------------------------------------
  # Public methods

  def _make_request_and_deserialize(self: "ApiClient", method: str, endpoint: str, **kwargs: Any) -> Any:
    r"""Make a request and deserialize the response.

    Args:
        method: HTTP method
        endpoint: API endpoint
        kwargs: Additional arguments for _make_request

    Returns:
        Deserialized response data, or the error handler's return value
    """
    response = self._make_request(method, endpoint, **kwargs)

    if not isinstance(response, httpx.Response):
      return response

    return self._deserialize_data(response)

  def get(self: "ApiClient", endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Make a GET request.

    Unvalidated: what is passed goes to ``bw serve`` as given, without the
    model checks a resource class makes first. ``bw serve`` can crash, or
    store the wrong thing, on a value it does not expect, so use a resource
    class where one covers the route.

    Args:
        endpoint: API endpoint
        params: Query parameters

    Returns:
        Deserialized response data; ``bytes`` for a downloaded file.
    """
    return self._make_request_and_deserialize('GET', endpoint, params=params)

  def post(self: "ApiClient", endpoint: str, data: RequestData = None, files: Optional[Dict[str, Any]] = None) -> Any:
    """Make a POST request.

    Unvalidated: what is passed goes to ``bw serve`` as given, without the
    model checks a resource class makes first. ``bw serve`` can crash, or
    store the wrong thing, on a value it does not expect, so use a resource
    class where one covers the route.

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

    Unvalidated: what is passed goes to ``bw serve`` as given, without the
    model checks a resource class makes first. ``bw serve`` can crash, or
    store the wrong thing, on a value it does not expect, so use a resource
    class where one covers the route.

    Args:
        endpoint: API endpoint
        data: Request body data

    Returns:
        Deserialized response data
    """
    return self._make_request_and_deserialize('PUT', endpoint, data=data)

  def delete(self: "ApiClient", endpoint: str) -> Any:
    """Make a DELETE request.

    Unvalidated: what is passed goes to ``bw serve`` as given, without the
    model checks a resource class makes first. ``bw serve`` can crash, or
    store the wrong thing, on a value it does not expect, so use a resource
    class where one covers the route.

    Args:
        endpoint: API endpoint

    Returns:
        Deserialized response data
    """
    return self._make_request_and_deserialize('DELETE', endpoint)
