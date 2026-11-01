"""Add, rename, get and delete a collection in an organization.

The vault must already be unlocked: start ``bw serve`` from a session
where ``bw unlock`` has run, as an account that may manage collections in
at least one organization. This script unlocks nothing itself.

Set ``BW_SERVE_URL`` to reach a ``bw serve`` somewhere other than
``http://localhost:8087``. Run it with::

    python examples/org_collections.py
"""

from __future__ import annotations

import os
import sys

from bw_serve_client import ApiClient
from bw_serve_client import ExternalServiceError
from bw_serve_client import Organizations
from bw_serve_client import OrgCollections
from bw_serve_client import UserError
from bw_serve_client import ValidationError


def main() -> int:
  """Walk one collection through its whole life, in the first organization.

  Returns:
    The process exit status.
  """
  base_url = os.environ.get("BW_SERVE_URL", "http://localhost:8087")

  with ApiClient(base_url=base_url) as client:
    collections = OrgCollections(client)

    try:
      existing = collections.list_collections()

    except ExternalServiceError as error:
      print(f"Cannot reach bw serve at {base_url}: {error}", file=sys.stderr)
      return 1

    except UserError as error:
      print(f"Unlock the vault first: {error}", file=sys.stderr)
      return 1

    print(f"The account can see {len(existing)} collections")

    organization_ids = [o.id for o in Organizations(client).list() if o.id is not None]

    if not organization_ids:
      print("The account belongs to no organization, so there is nowhere to add a collection")
      return 0

    organization_id = organization_ids[0]

    collection = collections.add(organization_id, "Example collection")
    collection_id = collection.id

    # bw serve returns the new collection with its id; the check is what
    # lets a type checker see that.
    if collection_id is None:
      print("bw serve returned the new collection without an id", file=sys.stderr)
      return 1

    print(f"Added {collection.name!r} with id {collection_id}")

    collections.modify(collection_id, organization_id, "Example collection, renamed")
    print(f"Renamed it to {collections.get(collection_id, organization_id).name!r}")

    collections.delete(collection_id, organization_id)
    print("Deleted it")

    # By default every failure raises. bw serve answers a get for a
    # collection that no longer exists with a 400, which is a
    # ValidationError.
    try:
      collections.get(collection_id, organization_id)

    except ValidationError as error:
      print(f"Getting it again fails as expected: {error} (HTTP {error.status_code})")

  return 0


if __name__ == "__main__":
  sys.exit(main())
