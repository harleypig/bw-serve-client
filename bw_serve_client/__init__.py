"""Bitwarden Vault Management API client package."""

# Default logging
import logging

from ._generated import models as _models
from ._generated.models import *  # noqa: F401,F403 - models.__all__ is the list, so it is never kept by hand.
from .api_client import ApiClient
from .errors import BitwardenError
from .errors import ExternalServiceError
from .errors import InternalError
from .errors import UserError
from .errors import ValidationError

__version__ = "0.1.1"
__all__ = ["ApiClient", "BitwardenError", "ValidationError", "UserError", "ExternalServiceError", "InternalError"]
__all__ += _models.__all__

logging.getLogger(__name__).addHandler(logging.NullHandler())
