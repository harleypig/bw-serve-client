"""Shared fixtures for the resource-class tests and the recorded payloads."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional, Protocol, TYPE_CHECKING

import httpx
import pytest

from bw_serve_client.api_client import ApiClient

if TYPE_CHECKING:
  from bw_serve_client.errors import BitwardenError

#: One recorded failure: category, message, status code, cause.
Call = tuple["type[BitwardenError]", str, Optional[int], Optional[BaseException]]


class MakeClient(Protocol):
  """Signature of the ``make_client`` fixture."""

  # A Protocol stub never reads its parameters, so U100 is suppressed on
  # each.
  def __call__(
    self: MakeClient,
    status: int = 200,  # noqa: U100
    json_body: Any = None,  # noqa: U100
    text_body: Optional[str] = None,  # noqa: U100
    **kwargs: Any,  # noqa: U100
  ) -> ApiClient:
    """Build an ApiClient whose transport answers every request alike.

    Args:
        status: HTTP status of every response.
        json_body: JSON body of every response.
        text_body: Plain-text body, used when ``json_body`` is None.
        kwargs: Passed on to :class:`ApiClient`.
    """
    ...


@pytest.fixture
def sent() -> list[httpx.Request]:
  """Every request a ``make_client`` client sends, in order."""
  return []


@pytest.fixture
def make_client(sent: list[httpx.Request]) -> MakeClient:
  """Build an ApiClient whose transport records requests into ``sent``.

  Every response has the given status and either ``json_body`` as JSON or
  ``text_body`` as plain text. Extra keyword arguments go to ApiClient.
  """

  def make(status: int = 200, json_body: Any = None, text_body: Optional[str] = None, **kwargs: Any) -> ApiClient:

    def handler(request: httpx.Request) -> httpx.Response:
      sent.append(request)

      if text_body is not None:
        return httpx.Response(status, text=text_body)

      return httpx.Response(status, json=json_body)

    return ApiClient(transport=httpx.MockTransport(handler), **kwargs)

  return make


class ReturningHandler:
  """Error handler that records each failure and returns a fixed object."""

  def __init__(self: ReturningHandler) -> None:
    self.result = object()
    self.calls: list[Call] = []

  def handle(
    self: ReturningHandler,
    category: type[BitwardenError],
    message: str,
    *,
    level: Optional[int] = None,  # noqa: U100 - part of the ErrorHandler protocol; not recorded.
    status_code: Optional[int] = None,
    cause: Optional[BaseException] = None,
  ) -> object:
    """Record the failure instead of raising it.

    Args:
      category: The failure's category.
      message: Description of the failure.
      level: Severity; unused.
      status_code: HTTP status, or None.
      cause: The triggering exception, or None.

    Returns:
      The fixed result object.
    """
    self.calls.append((category, message, status_code, cause))
    return self.result


@pytest.fixture
def returning_handler() -> ReturningHandler:
  """Provide a fresh error handler that returns instead of raising."""
  return ReturningHandler()


# -----------------------------------------------------------------------------
#: Where ``tests/fixtures/recorder/record.py`` writes one payload per case.
RECORDED_DIR = Path(__file__).parent / "fixtures" / "serve"


def load_recorded(name: str) -> dict[str, Any]:
  """Read one recorded bw serve payload.

  Args:
    name: The case name, which is the file stem under ``RECORDED_DIR``.

  Returns:
    The payload: ``case``, ``description``, ``recorded`` (CLI version,
    server image, date), ``request`` (method, path, body) and ``response``
    (status, body).
  """
  return json.loads((RECORDED_DIR / f"{name}.json").read_text())
