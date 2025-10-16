"""Bitwarden Vault Management API client package."""

# Default logging
import logging

from .api_client import (
  ApiClient,
  AuthenticationError,
  BitwardenAPIError,
  NotFoundError,
  ServerError,
  ValidationError,
)

__version__ = "0.1.1"
__all__ = [
  "ApiClient", "BitwardenAPIError", "AuthenticationError", "ValidationError",
  "NotFoundError", "ServerError"
]

logging.getLogger(__name__).addHandler(logging.NullHandler())
