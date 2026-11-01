"""Attach a file to an item, download it, and delete it through a running bw serve.

The vault must already be unlocked: start ``bw serve`` from a session
where ``bw unlock`` has run. This script unlocks nothing itself.

Pass the id of an item to attach the file to. Set ``BW_SERVE_URL`` to
reach a ``bw serve`` somewhere other than ``http://localhost:8087``. Run
it with::

    python examples/attachments.py <item id>
"""

from __future__ import annotations

import os
import sys

from bw_serve_client import ApiClient
from bw_serve_client import Attachments
from bw_serve_client import ExternalServiceError
from bw_serve_client import UserError
from bw_serve_client import ValidationError


def main() -> int:
  """Walk one attachment through its whole life.

  Returns:
    The process exit status.
  """
  if len(sys.argv) != 2:
    print(f"usage: {sys.argv[0]} <item id>", file=sys.stderr)
    return 2

  item_id = sys.argv[1]
  base_url = os.environ.get("BW_SERVE_URL", "http://localhost:8087")

  # Not valid UTF-8, so the download only matches if it is read as bytes.
  content = b"Example attachment\n\xff\xfe\x00\x01"

  with ApiClient(base_url=base_url) as client:
    attachments = Attachments(client)

    try:
      item = attachments.add(item_id, content, "example-attachment.bin")

    except ExternalServiceError as error:
      print(f"Cannot reach bw serve at {base_url}: {error}", file=sys.stderr)
      return 1

    except UserError as error:
      print(f"Unlock the vault first: {error}", file=sys.stderr)
      return 1

    added = [attachment for attachment in item.attachments or [] if attachment.file_name == "example-attachment.bin"]

    if not added or added[-1].id is None:
      print("bw serve returned the item without the new attachment", file=sys.stderr)
      return 1

    attachment_id = added[-1].id
    print(f"Attached {added[-1].file_name!r} ({added[-1].size_name}) with id {attachment_id}")

    downloaded = attachments.get(attachment_id, item_id)
    print(f"Downloaded {len(downloaded)} bytes; identical to the upload: {downloaded == content}")

    attachments.delete(attachment_id, item_id)
    print("Deleted it")

    # By default every failure raises. bw serve answers a download of an
    # attachment that no longer exists with a 400, which is a
    # ValidationError.
    try:
      attachments.get(attachment_id, item_id)

    except ValidationError as error:
      print(f"Downloading it again fails as expected: {error} (HTTP {error.status_code})")

  return 0


if __name__ == "__main__":
  sys.exit(main())
