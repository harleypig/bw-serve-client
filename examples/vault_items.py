"""Add, find, edit, archive, trash, restore and delete an item via bw serve.

The vault must already be unlocked: start ``bw serve`` from a session
where ``bw unlock`` has run. This script unlocks nothing itself.

Set ``BW_SERVE_URL`` to reach a ``bw serve`` somewhere other than
``http://localhost:8087``. Run it with::

    python examples/vault_items.py
"""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

from bw_serve_client import ApiClient
from bw_serve_client import ExternalServiceError
from bw_serve_client import UserError
from bw_serve_client import ValidationError
from bw_serve_client import VaultControl
from bw_serve_client import VaultItems

if TYPE_CHECKING:
  from uuid import UUID


# -----------------------------------------------------------------------------
def _archive(items: VaultItems, vault: VaultControl, item_id: UUID) -> None:
  """Archive the item and restore it from the archive.

  Args:
    items: The resource.
    vault: Syncs, so a list reflects the write before it.
    item_id: The item's id.
  """
  # Archiving needs a premium account, so bw serve may refuse it here.
  try:
    items.archive(item_id)
    vault.sync()
    print(f"Archived it; {len(items.list(archived=True))} archived items")

    items.restore(item_id)
    print("Restored it from the archive")

  except (ValidationError, UserError) as error:
    print(f"Archiving is not available here: {error}")


# -----------------------------------------------------------------------------
def _trash_and_delete(items: VaultItems, vault: VaultControl, item_id: UUID) -> None:
  """Trash the item, restore it, then delete it for good.

  Args:
    items: The resource.
    vault: Syncs, so a read reflects the write before it.
    item_id: The item's id.
  """
  items.delete(item_id)
  vault.sync()
  print(f"Moved it to the trash; {len(items.list(trash=True))} items there")

  items.restore(item_id)
  print("Restored it from the trash")

  items.delete(item_id, permanent=True)
  vault.sync()
  print("Deleted it permanently")

  # By default every failure raises. bw serve answers a get for an item
  # that no longer exists with a 400, which is a ValidationError.
  try:
    items.get(item_id)

  except ValidationError as error:
    print(f"Getting it again fails as expected: {error} (HTTP {error.status_code})")


# -----------------------------------------------------------------------------
def main() -> int:
  """Walk one secure note through its whole life.

  Returns:
    The process exit status.
  """
  base_url = os.environ.get("BW_SERVE_URL", "http://localhost:8087")

  with ApiClient(base_url=base_url) as client:
    items = VaultItems(client)
    vault = VaultControl(client)

    try:
      existing = items.list()

    except ExternalServiceError as error:
      print(f"bw serve at {base_url} failed: {error}", file=sys.stderr)
      return 1

    except UserError as error:
      print(f"Unlock the vault first: {error}", file=sys.stderr)
      return 1

    print(f"{len(existing)} items in the vault")

    note = items.add({"type": 2, "name": "Example note", "notes": "Made by examples/vault_items.py", "secureNote": {"type": 0}})
    item_id = note.id

    # bw serve always returns a new item with its id; the check is what
    # lets a type checker see that.
    if item_id is None:
      print("bw serve returned the new item without an id", file=sys.stderr)
      return 1

    print(f"Added {note.name!r} with id {item_id}")

    # bw serve's local state can lag its own writes, so a read straight
    # after one may not see it; a sync brings the local state up to date.
    vault.sync()

    # A search term finds it too, as long as it matches only this item.
    # bw serve answers an ambiguous search with a 400 listing the matches.
    try:
      print(f"Found by search: {items.get(search='Example note').name!r}")

    except ValidationError as error:
      if "more than one result" in str(error).lower():
        print(f"Search matched more than one item: {error}")

      else:
        print(f"Search did not find it: {error}")

    # The edit is get, change, put: the fetched item goes back whole, and
    # its server-side fields are dropped on the way.
    try:
      renamed = items.modify(item_id, items.get(item_id).model_copy(update={"name": "Example note, renamed"}))

    except ValidationError as error:
      print(f"Cannot read the new item back to edit it: {error}", file=sys.stderr)
      return 1

    print(f"Renamed it to {renamed.name!r}")

    _archive(items, vault, item_id)
    _trash_and_delete(items, vault, item_id)

  return 0


if __name__ == "__main__":
  sys.exit(main())
