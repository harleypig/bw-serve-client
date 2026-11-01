"""Read the fields of one login item through a running bw serve.

The vault must already be unlocked: start ``bw serve`` from a session
where ``bw unlock`` has run. This script unlocks nothing itself.

Pass the id of a login item in the vault. Set ``BW_SERVE_URL`` to reach a
``bw serve`` somewhere other than ``http://localhost:8087``. Run it with::

    python examples/item_fields.py 3a84be8d-12e7-4223-98cd-ae0000eabdec
"""

from __future__ import annotations

import os
import sys

from bw_serve_client import ApiClient
from bw_serve_client import ExternalServiceError
from bw_serve_client import ItemFields
from bw_serve_client import UserError
from bw_serve_client import ValidationError


def main() -> int:
  """Print what each field getter returns for the item named on the command line.

  Returns:
    The process exit status.
  """
  if len(sys.argv) != 2:
    print(f"usage: {sys.argv[0]} ITEM_ID", file=sys.stderr)
    return 2

  item_id = sys.argv[1]
  base_url = os.environ.get("BW_SERVE_URL", "http://localhost:8087")

  with ApiClient(base_url=base_url) as client:
    fields = ItemFields(client)

    try:
      print(f"Username: {fields.username(item_id)}")

    except ExternalServiceError as error:
      print(f"Cannot reach bw serve at {base_url}: {error}", file=sys.stderr)
      return 1

    except UserError as error:
      print(f"Unlock the vault first: {error}", file=sys.stderr)
      return 1

    except ValidationError as error:
      print(f"Cannot read item {item_id}: {error}", file=sys.stderr)
      return 1

    # The password is a SecretStr: printing it shows asterisks, and only
    # get_secret_value() reveals it. This prints its length and nothing more.
    password = fields.password(item_id)
    print(f"Password: {password} ({len(password.get_secret_value())} characters)")
    print(f"Exposed in {fields.exposed(item_id)} known breaches")

    # bw serve answers with a 400 when a field is empty, which by default
    # raises ValidationError.
    for name, getter in (("URI", fields.uri), ("Notes", fields.notes), ("TOTP code", fields.totp)):
      try:
        print(f"{name}: {getter(item_id)}")

      except ValidationError as error:
        print(f"{name}: none ({error})")

  return 0


if __name__ == "__main__":
  sys.exit(main())
