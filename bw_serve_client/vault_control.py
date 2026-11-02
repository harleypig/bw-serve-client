"""VaultControl domain class for the Bitwarden Vault Management API.

Mirrors the ``Lock & Unlock`` and ``Miscellaneous`` vault routes in the API
spec. One method per route:

  POST /lock   - VaultControl.lock
  POST /unlock - VaultControl.unlock
  POST /sync   - VaultControl.sync
  GET  /status - VaultControl.status
"""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING, Union

from ._generated.models import LockUnlockDataSchema
from ._generated.models import StatusDataSchema
from ._generated.models import SyncMessageSchema
from ._generated.models import SyncPostParameters
from ._generated.models import TemplateSchema
from ._generated.models import UnlockPostRequestSchema
from .errors import ExternalServiceError
from .resource import Resource
from .resource import route

if TYPE_CHECKING:
  from pydantic import SecretStr


class VaultControl(Resource):
  """Lock, unlock, sync and report the state of the vault ``bw serve`` holds.

  The master password and the session key are secrets: both travel as
  :class:`~pydantic.SecretStr`, so neither shows in a repr, a log record or
  an error message. Construction, logging and error handling are
  :class:`Resource`'s. Every method returns what the error handler
  returned, in place of its result, when a failure is handled without
  raising.
  """

  # ---------------------------------------------------------------------------
  @route("POST", "/lock")
  def lock(self: VaultControl) -> Union[LockUnlockDataSchema, Any]:
    """Lock your vault.

    Returns:
        bw serve's confirmation; its ``title`` reads "Your vault is
        locked."
    """
    return self._request("POST", "/lock", response_type=LockUnlockDataSchema)

  # ---------------------------------------------------------------------------
  @route("POST", "/unlock")
  def unlock(self: VaultControl, password: Union[str, SecretStr]) -> Union[SecretStr, Any]:
    """Unlock your vault.

    ``bw serve`` keeps the session itself, so the key returned need not be
    passed to any later call; it is returned for a caller that also drives
    the ``bw`` CLI (``BW_SESSION``).

    Args:
        password: The master password.

    Returns:
        The session key.
    """
    result = self._request(
      "POST", "/unlock", body=(UnlockPostRequestSchema, {
        "password": password
      }), response_type=LockUnlockDataSchema
    )

    if not isinstance(result, LockUnlockDataSchema):
      return result

    if result.raw is None:
      return self._fail(ExternalServiceError, "unlock succeeded but the response carries no session key")

    return result.raw

  # ---------------------------------------------------------------------------
  @route("POST", "/sync")
  def sync(self: VaultControl, force: Optional[bool] = None) -> Union[SyncMessageSchema, Any]:
    """Sync your vault.

    Args:
        force: Ignore the last-sync timestamp and re-sync everything.

    Returns:
        bw serve's confirmation; its ``title`` reads "Syncing complete."
    """
    return self._request("POST", "/sync", query=(SyncPostParameters, {"force": force}), response_type=SyncMessageSchema)

  # ---------------------------------------------------------------------------
  @route("GET", "/status")
  def status(self: VaultControl) -> Union[TemplateSchema, None, Any]:
    """Get the status of the Bitwarden CLI.

    Answers whether the vault is locked or not, so it works on a locked
    vault.

    Returns:
        The server URL, last sync, user email and id, and the vault's
        ``status``: locked, unlocked or unauthenticated.
    """
    result = self._request("GET", "/status", response_type=StatusDataSchema)

    return self._member(result, StatusDataSchema, "template")
