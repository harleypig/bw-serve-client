"""Check, sync, lock and unlock the vault through a running bw serve.

Start ``bw serve`` from a logged-in session. The master password is read
from the terminal and never echoed; the session key unlock returns is
never printed.

Set ``BW_SERVE_URL`` to reach a ``bw serve`` somewhere other than
``http://localhost:8087``. Run it with::

    python examples/vault_control.py
"""

from __future__ import annotations

from getpass import getpass
import os
import sys

from bw_serve_client import ApiClient
from bw_serve_client import ExternalServiceError
from bw_serve_client import UserError
from bw_serve_client import VaultControl


def main() -> int:
  """Report the vault's state, sync it, then lock and unlock it again.

  Returns:
    The process exit status.
  """
  base_url = os.environ.get("BW_SERVE_URL", "http://localhost:8087")

  with ApiClient(base_url=base_url) as client:
    vault = VaultControl(client)

    try:
      status = vault.status()

    except ExternalServiceError as error:
      print(f"bw serve at {base_url} failed: {error}", file=sys.stderr)
      return 1

    if status is None or status.status is None:
      print("bw serve reported no vault status", file=sys.stderr)
      return 1

    state = status.status.value
    print(f"{status.user_email} at {status.server_url}: {state}")

    if state == "unauthenticated":
      print("Log in with `bw login` before starting bw serve", file=sys.stderr)
      return 1

    if state == "unlocked":
      print(vault.sync().title)
      print(vault.lock().title)

    try:
      session = vault.unlock(getpass("Master password: "))

    except UserError as error:
      print(f"Unlock refused: {error}", file=sys.stderr)
      return 1

    # The key is a SecretStr; printing it shows asterisks, not the key.
    print(f"Unlocked; session key {session}")

  return 0


if __name__ == "__main__":
  sys.exit(main())
