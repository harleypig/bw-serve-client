"""Bitwarden Vault Management API client package."""

# Default logging
import logging

from .api_client import ApiClient
from .api_client import AuthenticationError
from .api_client import BitwardenAPIError
from .api_client import NotFoundError
from .api_client import ServerError
from .api_client import ValidationError

# from models import *

__version__ = "0.1.1"
__all__ = ["ApiClient", "BitwardenAPIError", "AuthenticationError", "ValidationError", "NotFoundError", "ServerError"]

logging.getLogger(__name__).addHandler(logging.NullHandler())
