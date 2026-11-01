"""List, add, edit, unprotect, get and delete a text Send through bw serve.

The vault must already be unlocked: start ``bw serve`` from a session
where ``bw unlock`` has run. This script unlocks nothing itself.

Set ``BW_SERVE_URL`` to reach a ``bw serve`` somewhere other than
``http://localhost:8087``. Run it with::

    python examples/sends.py
"""

from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone
import os
import sys

from bw_serve_client import ApiClient
from bw_serve_client import ExternalServiceError
from bw_serve_client import Sends
from bw_serve_client import UserError
from bw_serve_client import ValidationError


def main() -> int:
  """Walk one text Send through its whole life.

  Returns:
    The process exit status.
  """
  base_url = os.environ.get("BW_SERVE_URL", "http://localhost:8087")
  deletion_date = datetime.now(timezone.utc) + timedelta(days=7)

  with ApiClient(base_url=base_url) as client:
    sends = Sends(client)

    try:
      existing = sends.list()

    except ExternalServiceError as error:
      print(f"bw serve at {base_url} failed: {error}", file=sys.stderr)
      return 1

    except UserError as error:
      print(f"Unlock the vault first: {error}", file=sys.stderr)
      return 1

    print(f"{len(existing)} Sends in the vault")

    send = sends.add("Example send", "Shared through bw serve.", password="example password", deletion_date=deletion_date)
    send_id = send.id

    if send_id is None:
      print("bw serve returned the new Send without an id", file=sys.stderr)
      return 1

    print(f"Added {send.name!r} with id {send_id}, password set: {send.password_set}")

    # A modify replaces the whole Send, so every value to keep is passed
    # again -- the password included.
    sends.modify(
      send_id,
      "Example send, renamed",
      "Shared through bw serve.",
      hidden=True,
      password="example password",
      deletion_date=deletion_date
    )
    print(f"Renamed it to {sends.get(send_id).name!r}")

    unprotected = sends.remove_password(send_id)
    print(f"Removed its password; password set: {unprotected.password_set}")

    sends.delete(send_id)
    print("Deleted it")

    try:
      sends.get(send_id)

    except ValidationError as error:
      print(f"Getting it again fails as expected: {error} (HTTP {error.status_code})")

  return 0


if __name__ == "__main__":
  sys.exit(main())
