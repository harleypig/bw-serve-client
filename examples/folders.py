"""List, add, rename, get and delete a folder through a running bw serve.

The vault must already be unlocked: start ``bw serve`` from a session
where ``bw unlock`` has run. This script unlocks nothing itself.

Set ``BW_SERVE_URL`` to reach a ``bw serve`` somewhere other than
``http://localhost:8087``. Run it with::

    python examples/folders.py
"""

from __future__ import annotations

import os
import sys
from uuid import UUID

from bw_serve_client import ApiClient
from bw_serve_client import ExternalServiceError
from bw_serve_client import Folders
from bw_serve_client import UserError
from bw_serve_client import ValidationError


def main() -> int:
  """Walk one folder through its whole life.

  Returns:
    The process exit status.
  """
  base_url = os.environ.get("BW_SERVE_URL", "http://localhost:8087")

  with ApiClient(base_url=base_url) as client:
    folders = Folders(client)

    try:
      existing = folders.list()

    except ExternalServiceError as error:
      print(f"bw serve at {base_url} failed: {error}", file=sys.stderr)
      return 1

    except UserError as error:
      print(f"Unlock the vault first: {error}", file=sys.stderr)
      return 1

    print(f"{len(existing)} folders in the vault")

    folder = folders.add("Example folder")
    folder_id = folder.id

    # Only bw's built-in "No Folder" lacks a UUID (its id is ""), so a new
    # folder always has one; the check is what lets a type checker see that.
    if not isinstance(folder_id, UUID):
      print("bw serve returned the new folder without an id", file=sys.stderr)
      return 1

    print(f"Added {folder.name!r} with id {folder_id}")

    folders.modify(folder_id, "Example folder, renamed")
    print(f"Renamed it to {folders.get(folder_id).name!r}")

    folders.delete(folder_id)
    print("Deleted it")

    # By default every failure raises. bw serve answers a get for a
    # folder that no longer exists with a 400, which is a ValidationError.
    try:
      folders.get(folder_id)

    except ValidationError as error:
      print(f"Getting it again fails as expected: {error} (HTTP {error.status_code})")

  return 0


if __name__ == "__main__":
  sys.exit(main())
