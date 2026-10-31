"""The common base for resource classes, one per tag of the Vault Management API.

A resource method declares its route and models; ``Resource._request()``
does the rest -- validates the path, query and body against their pydantic
models, sends the body as JSON (or multipart when there are files),
unwraps ``bw serve``'s response envelope and parses the payload into the
response type. Every failure along the way goes to the error handler, and
when the handler returns instead of raising, its value is what the
resource method returns.
"""

from __future__ import annotations

from collections.abc import Mapping
import functools
import logging
from typing import Any, Optional, Tuple, Type, TYPE_CHECKING

import httpx
from pydantic import BaseModel
from pydantic import SecretStr
from pydantic import TypeAdapter
from pydantic import ValidationError as PydanticValidationError
from pydantic_core import to_jsonable_python

from .errors import ExternalServiceError
from .errors import ValidationError

if TYPE_CHECKING:
  from .api_client import ApiClient
  from .errors import BitwardenError
  from .errors import ErrorHandler

#: Raw input and the pydantic model it must validate against.
Unvalidated = Tuple[Type[BaseModel], Mapping[str, Any]]


# -----------------------------------------------------------------------------
@functools.lru_cache(maxsize=None)
def _adapter(response_type: Any) -> TypeAdapter[Any]:
  """Build, once per type, the adapter that parses a response payload.

  Args:
    response_type: A pydantic model, or a type such as ``list[Model]``.

  Returns:
    The cached adapter.
  """
  return TypeAdapter(response_type)


# -----------------------------------------------------------------------------
def _reveal(value: Any) -> Any:
  """Replace every ``SecretStr`` in a dumped model with its value.

  Args:
    value: A model dumped in python mode, or any part of one.

  Returns:
    The same structure, with secrets in the clear for sending.
  """
  if isinstance(value, SecretStr):
    return value.get_secret_value()

  if isinstance(value, dict):
    return {key: _reveal(item) for key, item in value.items()}

  if isinstance(value, list):
    return [_reveal(item) for item in value]

  return value


# -----------------------------------------------------------------------------
def _summarize(error: PydanticValidationError) -> str:
  """Describe a validation failure without the input that failed.

  The input can be a secret -- a master password under a misspelled field
  name, a session key in a response -- so only where and why are kept.

  Args:
    error: The pydantic failure.

  Returns:
    One ``location: reason`` entry per error, separated by semicolons.
  """
  details = error.errors(include_url=False, include_context=False, include_input=False)

  return "; ".join(f"{'.'.join(str(part) for part in detail['loc']) or '<root>'}: {detail['msg']}" for detail in details)


# -----------------------------------------------------------------------------
class Resource:
  """Base for the resource classes: request validation, parsing, failures.

  ``logger`` and ``error_handler`` default to the client's, so both can be
  configured once on the :class:`ApiClient` and overridden per resource.

  Args:
    client: Shared :class:`ApiClient` for HTTP transport.
    logger: Logger for this resource; the client's when ``None``.
    error_handler: Failure handler for this resource; the client's when ``None``.
  """

  def __init__(
    self: Resource,
    client: ApiClient,
    logger: Optional[logging.Logger] = None,
    error_handler: Optional[ErrorHandler] = None,
  ) -> None:
    self.client = client
    self.logger = logger if logger is not None else client.logger
    self.error_handler = error_handler if error_handler is not None else client.error_handler

  # ---------------------------------------------------------------------------
  def _fail(
    self: Resource,
    category: type[BitwardenError],
    message: str,
    *,
    status_code: Optional[int] = None,
    cause: Optional[BaseException] = None,
  ) -> Any:
    """Hand one failure to the error handler.

    Args:
      category: The failure's category.
      message: Human-readable description of the failure.
      status_code: HTTP status, or ``None`` when there was no response.
      cause: The exception that triggered the failure, if any.

    Returns:
      The handler's return value, when it does not raise.
    """
    return self.error_handler.handle(category, message, status_code=status_code, cause=cause)

  # ---------------------------------------------------------------------------
  def _request(
    self: Resource,
    method: str,
    path: str,
    *,
    path_params: Optional[Unvalidated] = None,
    query: Optional[Unvalidated] = None,
    body: Optional[Unvalidated] = None,
    files: Optional[dict[str, Any]] = None,
    response_type: Any = None,
  ) -> Any:
    """Validate, send, and parse one request.

    ``path`` is a template such as ``/object/folder/{id}``, filled from the
    validated ``path_params``. Query fields that are ``None`` are left
    out. ``body`` is sent as JSON, or as multipart form fields beside
    ``files`` when there are any.

    The response's ``data`` member is parsed into ``response_type``; a
    list envelope (``{"object": "list", "data": [...]}``) is unwrapped to
    its items first. With no ``response_type`` the body is not read.

    Args:
      method: HTTP method.
      path: Route path, with ``{name}`` placeholders for path parameters.
      path_params: Path parameters and their model.
      query: Query parameters and their model.
      body: Request body fields and their model.
      files: Files to upload as multipart.
      response_type: A model or ``list[Model]`` for ``data``; ``None`` returns ``None``.

    Returns:
      The parsed response, or the error handler's return value.
    """
    validated: dict[str, dict[str, Any]] = {}

    for name, unvalidated in (("path", path_params), ("query", query), ("body", body)):
      if unvalidated is None:
        continue

      model, fields = unvalidated

      # The failure is reported outside the except block, so the pydantic
      # error, which holds the input, is neither the cause nor the context.
      try:
        dumped = model.model_validate(dict(fields)).model_dump(by_alias=True, exclude_none=True)
        validated[name] = to_jsonable_python(_reveal(dumped))
        continue

      except PydanticValidationError as e:
        problems = _summarize(e)

      return self._fail(ValidationError, f"invalid {name} for {method} {path}: {problems}")

    endpoint = path.format(**validated.get("path", {}))

    self.logger.debug("%s %s", method, endpoint)

    response = self.client._make_request(
      method,
      endpoint,
      data=validated.get("body"),
      params=validated.get("query") or None,
      files=files,
      error_handler=self.error_handler
    )

    if not isinstance(response, httpx.Response):
      return response

    if response_type is None:
      return None

    return self._parse(response, response_type)

  # ---------------------------------------------------------------------------
  def _parse(self: Resource, response: httpx.Response, response_type: Any) -> Any:
    """Parse a 2xx response's ``data`` into ``response_type``.

    Args:
      response: A successful response.
      response_type: What ``data`` parses into.

    Returns:
      The parsed payload, or the error handler's return value.
    """
    payload = self.client._deserialize_data(response)

    # The body itself stays out of the message: on /unlock it holds the
    # session key.
    if not isinstance(payload, dict) or "data" not in payload:
      return self._fail(
        ExternalServiceError, f"response has no data member (a {type(payload).__name__} body)", status_code=response.status_code
      )

    data = payload["data"]

    if isinstance(data, dict) and data.get("object") == "list":
      data = data.get("data")

    try:
      return _adapter(response_type).validate_python(data)

    except PydanticValidationError as e:
      problems = _summarize(e)

    return self._fail(
      ExternalServiceError, f"response does not match {response_type!r}: {problems}", status_code=response.status_code
    )
