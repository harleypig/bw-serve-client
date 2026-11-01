"""The common base for resource classes, one per tag of the Vault Management API.

A resource method declares its route with ``@route``, which is how the
route coverage and docstring tests find it, and names its models;
``Resource._request()`` does the rest -- validates the path, query and
body against their pydantic models, sends the body as JSON (or multipart
when there are files), unwraps ``bw serve``'s response envelope and
parses the payload into the response type, or returns the raw body for a
download. Every failure along the way
goes to the error handler, and when the handler returns instead of
raising, its value is what the resource method returns.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
import functools
import logging
from typing import Any, NamedTuple, Optional, Tuple, Type, TYPE_CHECKING, TypeVar, Union

import httpx
from pydantic import BaseModel
from pydantic import RootModel
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

#: Raw input and the pydantic model it must validate against: a mapping of
#: fields, or for a ``RootModel`` (a bare JSON array body) its root value.
Unvalidated = Tuple[Type[BaseModel], Union[Mapping[str, Any], Sequence[Any]]]

_Method = TypeVar("_Method", bound=Callable[..., Any])

# Where route() records its declarations on the function.
_ROUTES_ATTRIBUTE = "_bw_routes"


# -----------------------------------------------------------------------------
class RouteKey(NamedTuple):
  """One spec operation, as a resource method declares it.

  Attributes:
    method: The HTTP method, upper case, as the spec spells it.
    path: The path template, exactly as the spec spells it.
  """

  method: str
  path: str

  def __str__(self: RouteKey) -> str:
    """Spell the route ``METHOD /path``, the form the exclusion list uses.

    Returns:
      The method and path, separated by a space.
    """
    return f"{self.method} {self.path}"


# -----------------------------------------------------------------------------
def route(method: str, path: str) -> Callable[[_Method], _Method]:
  """Declare the spec route a resource method implements.

  The function is returned unchanged; the declaration is only recorded on
  it. Stack the decorator when one method dispatches to several routes.
  Nothing is normalized: ``method`` and ``path`` must match the spec's
  spelling, or the route coverage test reports the route as unknown.

  Args:
    method: The HTTP method, upper case.
    path: The path template, with the spec's ``{name}`` parameters.

  Returns:
    A decorator that records the route and returns the method.
  """
  key = RouteKey(method, path)

  def decorate(func: _Method) -> _Method:
    setattr(func, _ROUTES_ATTRIBUTE, (key, *declared_routes(func)))
    return func

  return decorate


# -----------------------------------------------------------------------------
def declared_routes(func: Any) -> Tuple[RouteKey, ...]:
  """Return the routes ``@route`` recorded on a function.

  Args:
    func: Any object; a resource method, usually.

  Returns:
    The declared routes, outermost decorator first; empty when none.
  """
  return getattr(func, _ROUTES_ATTRIBUTE, ())


# -----------------------------------------------------------------------------
def routed_methods(resource_class: type) -> dict[str, Tuple[RouteKey, ...]]:
  """Map each route-declaring method a class defines to its routes.

  Only the class's own namespace is read, so a method inherited from
  another resource class is reported once, by the class that defines it.

  Args:
    resource_class: A resource class.

  Returns:
    Method name to declared routes, for every method that declares any.
  """
  return {name: routes for name, value in vars(resource_class).items() if (routes := declared_routes(value))}


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
  @staticmethod
  def _member(result: Any, model: type[BaseModel], name: str) -> Any:
    """Take one member of a parsed response, passing a handler's value through.

    Args:
      result: ``_request``'s return: the parsed model, or a handler's value.
      model: The response type ``_request`` was given.
      name: The member to return.

    Returns:
      The member when ``result`` is a ``model``; otherwise ``result``,
      untouched.
    """
    return getattr(result, name) if isinstance(result, model) else result

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
    ``files`` when there are any; a ``RootModel`` body takes its root value
    as given, such as a list of ids, and is sent as that bare value.

    The response's ``data`` member is parsed into ``response_type``; a
    list envelope (``{"object": "list", "data": [...]}``) is unwrapped to
    its items first. ``bytes`` returns the body itself, unparsed. With no
    ``response_type`` the body is not read.

    Args:
      method: HTTP method.
      path: Route path, with ``{name}`` placeholders for path parameters.
      path_params: Path parameters and their model.
      query: Query parameters and their model.
      body: Request body fields and their model.
      files: Files to upload as multipart.
      response_type: A model or ``list[Model]`` for ``data``, or ``bytes``.

    Returns:
      The parsed response, or the error handler's return value.
    """
    validated: dict[str, Any] = {}

    for name, unvalidated in (("path", path_params), ("query", query), ("body", body)):
      if unvalidated is None:
        continue

      model, fields = unvalidated

      # The failure is reported outside the except block, so the pydantic
      # error, which holds the input, is neither the cause nor the context.
      try:
        raw = fields if issubclass(model, RootModel) else dict(fields)
        dumped = model.model_validate(raw).model_dump(by_alias=True, exclude_none=True)
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

    A ``bytes`` response is a download: the body is the file, whatever its
    content type, and is returned raw, since decoding it as text would
    corrupt anything that is not UTF-8.

    Args:
      response: A successful response.
      response_type: What ``data`` parses into, or ``bytes``.

    Returns:
      The parsed payload, or the error handler's return value.
    """
    if response_type is bytes:
      return response.content

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
