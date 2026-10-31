"""Bitwarden Vault Management API client package."""

# Default logging
import logging

from ._generated import models as _models
from ._generated.models import *  # noqa: F401,F403 - models.__all__ is the list, so it is never kept by hand.
from .api_client import ApiClient
from .errors import BitwardenError
from .errors import DefaultErrorHandler
from .errors import ErrorHandler
from .errors import ExternalServiceError
from .errors import InternalError
from .errors import UserError
from .errors import ValidationError
from .folders import Folder
from .folders import Folders

__version__ = "0.1.1"
# The documented surface: what a caller constructs, injects, catches and
# receives. Resource and category_for_status stay internal, and of the
# generated package only the models are public -- never ROUTES or Route.
__all__ = [
  "ApiClient",
  "ErrorHandler",
  "DefaultErrorHandler",
  "BitwardenError",
  "ValidationError",
  "UserError",
  "ExternalServiceError",
  "InternalError",
  "Folders",
  "Folder",
]
__all__ += _models.__all__

logging.getLogger(__name__).addHandler(logging.NullHandler())
