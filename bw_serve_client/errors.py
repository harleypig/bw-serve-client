"""Typed errors, an injectable error handler, and the default logger.

Every failure the library reports is one of four categories under the
common base :class:`BitwardenError`:

- :class:`ValidationError` -- the request was wrong: bad parameters, a body
  that does not validate, an id or path that names nothing.
- :class:`UserError` -- the request was fine but the user's side is not: a
  locked vault, a wrong master password.
- :class:`ExternalServiceError` -- ``bw serve`` failed us: a 5xx, a refused
  or dropped connection, a timeout, a response that does not parse.
- :class:`InternalError` -- a bug in this library. This is the contract's
  *system* category; it is not named ``SystemError`` because that would
  shadow the builtin.

The handler is the one place a failure becomes either a raised exception
or a returned value. A caller injects anything satisfying
:class:`ErrorHandler`; without one, :class:`DefaultErrorHandler` builds the
typed error, logs it if its level clears the log-level threshold, and
raises it if its level clears the error-level threshold, otherwise returns
it. Both thresholds are stdlib ``logging`` levels, so one scale serves
both.

Each category carries a default severity, its ``default_level``:
``ValidationError`` and ``UserError`` are ``WARNING``, since the caller can
correct the request or the vault state; ``ExternalServiceError`` and
``InternalError`` are ``ERROR``. The default error-level threshold is
``WARNING``, so every error raises out of the box; a caller that passes
``error_level=logging.ERROR`` gets validation and user errors returned
instead, while service failures and bugs still raise.

How an HTTP outcome maps to a category. ``category_for_status()`` is the
one implementation of the status rows; the rest are decided where the
failure happens:

+--------------------------------+--------------------------+
| Outcome                        | Category                 |
+================================+==========================+
| 400 saying the vault is locked | ``UserError``            |
| or no user is logged in, or    |                          |
| that the master password did   |                          |
| not decrypt the vault          |                          |
+--------------------------------+--------------------------+
| 400 and other unlisted 4xx     | ``ValidationError``      |
+--------------------------------+--------------------------+
| 401, 403                       | ``UserError``            |
+--------------------------------+--------------------------+
| 404                            | ``ValidationError``      |
+--------------------------------+--------------------------+
| 5xx                            | ``ExternalServiceError`` |
+--------------------------------+--------------------------+
| connection failure, timeout    | ``ExternalServiceError`` |
+--------------------------------+--------------------------+
| a URL httpx cannot build       | ``ValidationError``      |
+--------------------------------+--------------------------+
| 2xx body that does not parse   | ``ExternalServiceError`` |
+--------------------------------+--------------------------+
| a bug in this library          | ``InternalError``        |
+--------------------------------+--------------------------+

``bw serve`` answers every failed command with a 400 and a
``{"success": false, "message": ...}`` body, a locked vault included, so
the message is the only thing that tells a user-side state from a bad
request. It has no endpoint authentication, so a 401/403 can only mean a
user-side state too. A 404 means the caller's id or path names nothing,
which is a fault in the request rather than in the user's vault state; the
status code is kept on the error for a caller that needs to tell it apart
from a 400.
"""

from __future__ import annotations

import logging
from typing import Protocol

#: Package-default logger. No handler is attached here; the package adds a
#: ``NullHandler`` to its root logger and configuration is the caller's.
default_logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
class BitwardenError(Exception):
  """Base of every error this library builds.

  ``level`` is a stdlib ``logging`` level, which the handler compares
  against its thresholds; when not given it is the class's
  ``default_level``. ``status_code`` is ``None`` when there was no HTTP
  response, as with a connection failure or a bug.

  Args:
    message: Human-readable description of the failure.
    level: Severity as a ``logging`` level, or ``None`` for ``default_level``.
    status_code: HTTP status of the response, or ``None``.

  Attributes:
    default_level: Severity used when no ``level`` is given.
  """

  default_level: int = logging.ERROR

  def __init__(self: BitwardenError, message: str, level: int | None = None, status_code: int | None = None) -> None:
    if level is None:
      level = self.default_level

    # pickle and copy rebuild an exception as cls(*args), so args must
    # match this signature positionally.
    super().__init__(message, level, status_code)
    self.message = message
    self.level = level
    self.status_code = status_code

  def __str__(self: BitwardenError) -> str:
    """Render as the message alone, not the args tuple.

    Returns:
      The message.
    """
    return self.message


class ValidationError(BitwardenError):
  """The request was invalid: parameters, body, or an id naming nothing.

  Attributes:
    default_level: ``WARNING``; the caller can correct the request.
  """

  default_level = logging.WARNING


class UserError(BitwardenError):
  """The user's side blocks the request: locked vault, wrong password.

  Attributes:
    default_level: ``WARNING``; the caller can correct the vault state.
  """

  default_level = logging.WARNING


class ExternalServiceError(BitwardenError):
  """``bw serve`` failed: 5xx, connection failure, unparseable response."""


class InternalError(BitwardenError):
  """A bug in this library; the contract's *system* error category."""


# -----------------------------------------------------------------------------
# The messages bw serve sends, with a 400, when the vault is locked or no
# user is logged in (``errorIfLocked`` in the CLI's serve configurator), or
# when POST /unlock is given a wrong master password (recorded from CLI
# 2026.10.1). Each is matched as a substring of the lowercased message, on
# a 400 from any route, so trailing punctuation can drift. The password
# message is the full phrase rather than a bare "decryption", which would
# catch more; but there is no route context here, so the same crypto
# message on a 400 from any other route is a UserError too.
_USER_STATE_MESSAGES = ("vault is locked", "not logged in", "cryptography error, the decryption operation failed")


def category_for_status(status_code: int, message: str = "") -> type[BitwardenError]:
  """Choose the error category for an HTTP error status.

  Args:
    status_code: An HTTP status of 400 or above.
    message: The ``message`` from the response body, if it had one.

  Returns:
    The :class:`BitwardenError` subclass for that outcome, per the table
    in this module's docstring.
  """
  if status_code >= 500:
    return ExternalServiceError

  if status_code in (401, 403):
    return UserError

  if status_code == 400 and any(text in message.lower() for text in _USER_STATE_MESSAGES):
    return UserError

  return ValidationError


# -----------------------------------------------------------------------------
class ErrorHandler(Protocol):
  """What an injected error handler must provide.

  An implementation may return any object, including one of its own error
  types; raising instead of returning is equally valid. The library calls
  ``handle`` without ``level``; an implementation that compares severities
  should read ``None`` as the category's ``default_level``, as
  :class:`DefaultErrorHandler` does.
  """

  # A Protocol stub declares the parameters for implementers; its body
  # never reads them, so U100 is suppressed on each.
  def handle(
    self: ErrorHandler,
    category: type[BitwardenError],  # noqa: U100
    message: str,  # noqa: U100
    *,
    level: int | None = None,  # noqa: U100
    status_code: int | None = None,  # noqa: U100
    cause: BaseException | None = None,  # noqa: U100
  ) -> object:
    """Turn one failure into a raised exception or a returned value.

    Args:
      category: The failure's category, a :class:`BitwardenError` subclass.
      message: Human-readable description of the failure.
      level: Severity as a stdlib ``logging`` level; ``None`` means the category's ``default_level``.
      status_code: HTTP status, or ``None`` when there was no response.
      cause: The exception that triggered the failure, if any.
    """
    ...


# -----------------------------------------------------------------------------
class DefaultErrorHandler:
  """Build the typed error; log and raise it according to two thresholds.

  The logger defaults to ``default_logger``; an injected logger's own
  level and handlers are never changed. Errors at or above
  ``error_level`` are raised and those below it returned; errors at or
  above ``log_level`` are logged first. With the default ``error_level``
  of ``WARNING`` every category raises; ``error_level=logging.ERROR``
  returns validation and user errors.

  Args:
    logger: Where handled errors are logged.
    error_level: The ``logging`` level at which errors are raised.
    log_level: The ``logging`` level at which errors are logged.
  """

  def __init__(
    self: DefaultErrorHandler,
    logger: logging.Logger | None = None,
    error_level: int = logging.WARNING,
    log_level: int = logging.WARNING,
  ) -> None:
    self.logger = logger if logger is not None else default_logger
    self.error_level = error_level
    self.log_level = log_level

  def handle(
    self: DefaultErrorHandler,
    category: type[BitwardenError],
    message: str,
    *,
    level: int | None = None,
    status_code: int | None = None,
    cause: BaseException | None = None,
  ) -> BitwardenError:
    """Build a ``category`` error, log it, then raise or return it.

    Args:
      category: The failure's category, a :class:`BitwardenError` subclass.
      message: Human-readable description of the failure.
      level: ``logging`` level; ``None`` takes the category's ``default_level``.
      status_code: HTTP status, or ``None`` when there was no response.
      cause: The triggering exception, kept as the error's ``__cause__``.

    Returns:
      The built error, when its level is below ``error_level``.

    Raises:
      error: The built error, when its level reaches ``error_level``.
    """
    error = category(message, level=level, status_code=status_code)
    error.__cause__ = cause

    if error.level >= self.log_level:
      self.logger.log(error.level, "%s: %s", category.__name__, message)

    if error.level >= self.error_level:
      raise error

    return error
