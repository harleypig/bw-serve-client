"""List the organizations the account belongs to, and their members.

The vault must already be unlocked: start ``bw serve`` from a session
where ``bw unlock`` has run. This script unlocks nothing itself, and
changes nothing in the vault.

Set ``BW_SERVE_URL`` to reach a ``bw serve`` somewhere other than
``http://localhost:8087``. Run it with::

    python examples/organizations.py
"""

from __future__ import annotations

import os
import sys

from bw_serve_client import ApiClient
from bw_serve_client import ExternalServiceError
from bw_serve_client import Organizations
from bw_serve_client import UserError
from bw_serve_client import ValidationError


def main() -> int:
  """Print every organization, and the members of each.

  Returns:
    The process exit status.
  """
  base_url = os.environ.get("BW_SERVE_URL", "http://localhost:8087")

  with ApiClient(base_url=base_url) as client:
    organizations = Organizations(client)

    try:
      found = organizations.list()

    except ExternalServiceError as error:
      print(f"bw serve at {base_url} failed: {error}", file=sys.stderr)
      return 1

    except UserError as error:
      print(f"Unlock the vault first: {error}", file=sys.stderr)
      return 1

    print(f"The account belongs to {len(found)} organizations")

    for listed in found:
      # A listed organization always has an id; the check is what lets a
      # type checker see that.
      if listed.id is None:
        continue

      organization = organizations.get(listed.id)
      print(f"{organization.name} ({organization.id}), enabled: {organization.enabled}")

      # Listing members needs a role that may see them; bw serve answers
      # a 400 otherwise, which is a ValidationError.
      try:
        members = organizations.list_members(listed.id)

      except ValidationError as error:
        print(f"  Cannot list its members: {error}")
        continue

      for member in members:
        print(f"  {member.name} <{member.email}>, status {member.status}")

  return 0


if __name__ == "__main__":
  sys.exit(main())
