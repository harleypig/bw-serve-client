"""Tests for the error and logging module."""

from __future__ import annotations

import copy
import logging
import pickle
from typing import TYPE_CHECKING

import pytest

from bw_serve_client import errors
from bw_serve_client.errors import BitwardenError
from bw_serve_client.errors import category_for_status
from bw_serve_client.errors import DefaultErrorHandler
from bw_serve_client.errors import ErrorHandler
from bw_serve_client.errors import ExternalServiceError
from bw_serve_client.errors import InternalError
from bw_serve_client.errors import UserError
from bw_serve_client.errors import ValidationError

if TYPE_CHECKING:
  from collections.abc import Callable

CATEGORIES = [ValidationError, UserError, ExternalServiceError, InternalError]
# The request or the vault state is the caller's to correct.
WARNING_CATEGORIES = [ValidationError, UserError]
# bw serve failed, or this library has a bug.
ERROR_CATEGORIES = [ExternalServiceError, InternalError]


# -----------------------------------------------------------------------------
class TestErrorTypes:
  """Tests for the typed error hierarchy."""

  @pytest.mark.parametrize("category", CATEGORIES)
  def test_category_is_a_bitwarden_error(self: TestErrorTypes, category: type[BitwardenError]) -> None:
    """Every category shares the common base."""
    assert issubclass(category, BitwardenError)

  def test_categories_are_distinct(self: TestErrorTypes) -> None:
    """No category is a subclass of another."""
    for category in CATEGORIES:
      others = [other for other in CATEGORIES if other is not category]
      assert not issubclass(category, tuple(others))

  def test_does_not_shadow_builtin_system_error(self: TestErrorTypes) -> None:
    """The system category does not reuse the builtin SystemError name."""
    assert not hasattr(errors, "SystemError")

  def test_carries_message_level_and_status(self: TestErrorTypes) -> None:
    """The error keeps what it was built with."""
    error = UserError("vault is locked", level=logging.WARNING, status_code=401)

    assert str(error) == "vault is locked"
    assert error.message == "vault is locked"
    assert error.level == logging.WARNING
    assert error.status_code == 401

  @pytest.mark.parametrize(
    ("category", "level"),
    [
      (ValidationError, logging.WARNING),
      (UserError, logging.WARNING),
      (ExternalServiceError, logging.ERROR),
      (InternalError, logging.ERROR),
    ],
  )
  def test_defaults_to_category_level_and_no_status(self: TestErrorTypes, category: type[BitwardenError], level: int) -> None:
    """Level defaults to the category's severity and status to None."""
    error = category("boom")

    assert error.level == level
    assert error.status_code is None

  @pytest.mark.parametrize("category", CATEGORIES)
  def test_explicit_level_overrides_category_default(self: TestErrorTypes, category: type[BitwardenError]) -> None:
    """A level passed in wins over the category's default."""
    assert category("boom", level=logging.CRITICAL).level == logging.CRITICAL

  # The pickle round-trip reads only bytes this test just wrote, never
  # untrusted data, so the unsafe-load rules do not apply.
  @pytest.mark.parametrize("clone", [copy.copy, lambda error: pickle.loads(pickle.dumps(error))])  # noqa: DUO103,SCS113
  def test_survives_pickle_and_copy(self: TestErrorTypes, clone: Callable[[BitwardenError], BitwardenError]) -> None:
    """Pickle and copy rebuild the error with every field."""
    error = clone(UserError("vault is locked", logging.WARNING, 401))

    assert type(error) is UserError
    assert str(error) == "vault is locked"
    assert (error.level, error.status_code) == (logging.WARNING, 401)


# -----------------------------------------------------------------------------
class TestCategoryForStatus:
  """Tests for the one mapping from an HTTP error status to a category."""

  @pytest.mark.parametrize(
    ("status", "category"),
    [
      (400, ValidationError),
      (401, UserError),
      (403, UserError),
      (404, ValidationError),
      (409, ValidationError),
      (418, ValidationError),
      (500, ExternalServiceError),
      (502, ExternalServiceError),
      (503, ExternalServiceError),
    ],
  )
  def test_maps_status(self: TestCategoryForStatus, status: int, category: type[BitwardenError]) -> None:
    """Each status maps to the category in the module's table."""
    assert category_for_status(status, "Bad request.") is category

  # The two messages bw serve's errorIfLocked sends, verbatim, and a case
  # variant to pin the case-insensitive match.
  @pytest.mark.parametrize("message", ["Vault is locked.", "You are not logged in.", "VAULT IS LOCKED"])
  def test_locked_or_logged_out_400_is_user_error(self: TestCategoryForStatus, message: str) -> None:
    """A 400 saying the vault is locked or no one is logged in is a user error."""
    assert category_for_status(400, message) is UserError

  def test_wrong_master_password_400_is_user_error(self: TestCategoryForStatus) -> None:
    """The 400 bw serve sends for a wrong master password is a user error."""
    assert category_for_status(400, "Cryptography error, The decryption operation failed") is UserError

  def test_other_cryptography_400_is_validation_error(self: TestCategoryForStatus) -> None:
    """Only the whole wrong-password message matches, not any crypto 400."""
    assert category_for_status(400, "Cryptography error, Invalid key") is ValidationError

  def test_locked_message_only_matters_on_400(self: TestCategoryForStatus) -> None:
    """A 5xx stays a service error whatever its message says."""
    assert category_for_status(500, "Vault is locked.") is ExternalServiceError

  def test_message_defaults_to_empty(self: TestCategoryForStatus) -> None:
    """With no message, a 400 is a validation error."""
    assert category_for_status(400) is ValidationError


# -----------------------------------------------------------------------------
class TestDefaultErrorHandler:
  """Tests for the built-in error handler."""

  @pytest.mark.parametrize("category", CATEGORIES)
  def test_returns_typed_error_below_error_level(self: TestDefaultErrorHandler, category: type[BitwardenError]) -> None:
    """Below the error level the typed error is returned."""
    handler = DefaultErrorHandler(error_level=logging.CRITICAL)

    error = handler.handle(category, "boom", status_code=500)

    assert type(error) is category
    assert error.message == "boom"
    assert error.status_code == 500

  @pytest.mark.parametrize("category", CATEGORIES)
  def test_raises_typed_error_at_error_level(self: TestDefaultErrorHandler, category: type[BitwardenError]) -> None:
    """At the error level the typed error is raised."""
    handler = DefaultErrorHandler(error_level=logging.ERROR)

    with pytest.raises(category, match="boom"):
      handler.handle(category, "boom", level=logging.ERROR)

  def test_raises_above_error_level(self: TestDefaultErrorHandler) -> None:
    """Above the error level the typed error is raised."""
    handler = DefaultErrorHandler(error_level=logging.WARNING)

    with pytest.raises(ValidationError):
      handler.handle(ValidationError, "bad id", level=logging.ERROR)

  def test_default_error_level_is_warning(self: TestDefaultErrorHandler) -> None:
    """The default threshold is WARNING."""
    assert DefaultErrorHandler().error_level == logging.WARNING

  @pytest.mark.parametrize("category", CATEGORIES)
  def test_default_error_level_raises_every_category(self: TestDefaultErrorHandler, category: type[BitwardenError]) -> None:
    """Out of the box every category raises at its own default level."""
    with pytest.raises(category):
      DefaultErrorHandler().handle(category, "boom")

  @pytest.mark.parametrize("category", WARNING_CATEGORIES)
  def test_error_threshold_returns_validation_and_user_errors(
    self: TestDefaultErrorHandler, category: type[BitwardenError]
  ) -> None:
    """At an ERROR threshold, validation and user errors are returned."""
    error = DefaultErrorHandler(error_level=logging.ERROR).handle(category, "boom")

    assert type(error) is category
    assert error.level == logging.WARNING

  @pytest.mark.parametrize("category", ERROR_CATEGORIES)
  def test_error_threshold_raises_service_and_internal_errors(
    self: TestDefaultErrorHandler, category: type[BitwardenError]
  ) -> None:
    """At an ERROR threshold, service failures and bugs still raise."""
    with pytest.raises(category):
      DefaultErrorHandler(error_level=logging.ERROR).handle(category, "boom")

  def test_explicit_level_overrides_category_default(self: TestDefaultErrorHandler) -> None:
    """A level passed to handle wins over the category's default."""
    with pytest.raises(ValidationError) as excinfo:
      DefaultErrorHandler(error_level=logging.ERROR).handle(ValidationError, "bad id", level=logging.ERROR)

    assert excinfo.value.level == logging.ERROR

  def test_returned_error_keeps_cause(self: TestDefaultErrorHandler) -> None:
    """A returned error carries the triggering exception."""
    cause = ConnectionError("refused")
    handler = DefaultErrorHandler(error_level=logging.CRITICAL)

    error = handler.handle(ExternalServiceError, "down", cause=cause)

    assert error.__cause__ is cause

  def test_raised_error_keeps_cause(self: TestDefaultErrorHandler) -> None:
    """A raised error carries the triggering exception."""
    cause = ConnectionError("refused")

    with pytest.raises(ExternalServiceError) as excinfo:
      DefaultErrorHandler().handle(ExternalServiceError, "down", cause=cause)

    assert excinfo.value.__cause__ is cause


# -----------------------------------------------------------------------------
class TestDefaultErrorHandlerLogging:
  """Tests for the log-level threshold and the logger choice."""

  def test_logs_at_or_above_log_level(self: TestDefaultErrorHandlerLogging, caplog: pytest.LogCaptureFixture) -> None:
    """A failure at the log level is logged once."""
    handler = DefaultErrorHandler(error_level=logging.CRITICAL, log_level=logging.WARNING)

    with caplog.at_level(logging.DEBUG, logger=errors.__name__):
      handler.handle(UserError, "vault is locked", level=logging.WARNING)

    assert caplog.record_tuples == [(errors.__name__, logging.WARNING, "UserError: vault is locked")]

  def test_skips_below_log_level(self: TestDefaultErrorHandlerLogging, caplog: pytest.LogCaptureFixture) -> None:
    """A failure below the log level is not logged."""
    handler = DefaultErrorHandler(error_level=logging.CRITICAL, log_level=logging.ERROR)

    with caplog.at_level(logging.DEBUG, logger=errors.__name__):
      handler.handle(UserError, "vault is locked", level=logging.WARNING)

    assert caplog.records == []

  def test_logs_before_raising(self: TestDefaultErrorHandlerLogging, caplog: pytest.LogCaptureFixture) -> None:
    """A raised failure is still logged."""
    with caplog.at_level(logging.DEBUG, logger=errors.__name__), pytest.raises(InternalError):
      DefaultErrorHandler().handle(InternalError, "bug")

    assert caplog.record_tuples == [(errors.__name__, logging.ERROR, "InternalError: bug")]

  def test_logs_at_category_default_level(self: TestDefaultErrorHandlerLogging, caplog: pytest.LogCaptureFixture) -> None:
    """With no level given, the record carries the category's severity."""
    handler = DefaultErrorHandler(error_level=logging.CRITICAL)

    with caplog.at_level(logging.DEBUG, logger=errors.__name__):
      handler.handle(ValidationError, "bad id")

    assert caplog.record_tuples == [(errors.__name__, logging.WARNING, "ValidationError: bad id")]

  def test_log_threshold_skips_warning_categories(self: TestDefaultErrorHandlerLogging, caplog: pytest.LogCaptureFixture) -> None:
    """A log level of ERROR skips a validation error at its default level."""
    handler = DefaultErrorHandler(error_level=logging.CRITICAL, log_level=logging.ERROR)

    with caplog.at_level(logging.DEBUG, logger=errors.__name__):
      handler.handle(UserError, "vault is locked")
      handler.handle(ExternalServiceError, "down")

    assert caplog.record_tuples == [(errors.__name__, logging.ERROR, "ExternalServiceError: down")]

  def test_default_logger_is_module_logger(self: TestDefaultErrorHandlerLogging) -> None:
    """Without an injected logger the module logger is used."""
    assert DefaultErrorHandler().logger is logging.getLogger("bw_serve_client.errors")

  def test_default_logger_has_no_handlers_of_its_own(self: TestDefaultErrorHandlerLogging) -> None:
    """The module adds no handler to its logger."""
    assert errors.default_logger.handlers == []

  def test_uses_injected_logger(self: TestDefaultErrorHandlerLogging, caplog: pytest.LogCaptureFixture) -> None:
    """An injected logger receives the record."""
    logger = logging.getLogger("test_errors.injected")
    handler = DefaultErrorHandler(logger=logger, error_level=logging.CRITICAL)

    with caplog.at_level(logging.DEBUG):
      handler.handle(ValidationError, "bad id", level=logging.ERROR)

    assert caplog.record_tuples == [("test_errors.injected", logging.ERROR, "ValidationError: bad id")]

  def test_does_not_change_injected_logger_level(self: TestDefaultErrorHandlerLogging) -> None:
    """The handler leaves an injected logger level alone."""
    logger = logging.getLogger("test_errors.untouched")
    logger.setLevel(logging.CRITICAL)

    DefaultErrorHandler(logger=logger, log_level=logging.DEBUG)

    assert logger.level == logging.CRITICAL


# -----------------------------------------------------------------------------
class _CollectingHandler:
  """A caller-supplied handler that returns its own objects, never raising."""

  def __init__(self: _CollectingHandler) -> None:
    self.seen: list[tuple[object, ...]] = []

  def handle(
    self: _CollectingHandler,
    category: type[BitwardenError],
    message: str,
    *,
    level: int = logging.ERROR,
    status_code: int | None = None,
    cause: BaseException | None = None,
  ) -> object:
    """Record the failure and return a plain dict.

    Args:
      category: The failure's category.
      message: Description of the failure.
      level: Severity level.
      status_code: HTTP status, if any.
      cause: Triggering exception, if any.

    Returns:
      A dict describing the failure.
    """
    self.seen.append((category, message, status_code))
    return {"category": category.__name__, "message": message, "level": level, "cause": cause}


class TestInjectedHandler:
  """Tests that a caller's own handler satisfies the protocol."""

  def test_custom_handler_satisfies_protocol(self: TestInjectedHandler) -> None:
    """A caller handler returning its own objects is accepted."""
    collector = _CollectingHandler()
    handler: ErrorHandler = collector

    result = handler.handle(UserError, "bad password", level=logging.CRITICAL, status_code=403)

    assert result == {"category": "UserError", "message": "bad password", "level": logging.CRITICAL, "cause": None}
    assert collector.seen == [(UserError, "bad password", 403)]

  def test_default_handler_satisfies_protocol(self: TestInjectedHandler) -> None:
    """The built-in handler satisfies the protocol."""
    handler: ErrorHandler = DefaultErrorHandler(error_level=logging.CRITICAL)

    assert isinstance(handler.handle(InternalError, "bug"), InternalError)
