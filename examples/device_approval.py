"""List the pending trusted-device requests of each organization.

Device approval exists only in the licensed (commercial) Bitwarden CLI
build. On the open-source ``bw``, ``bw serve`` has no such route and
answers 404, which this script reports.

The vault must already be unlocked: start ``bw serve`` from a session
where ``bw unlock`` has run. This script unlocks nothing itself, and
approves or denies nothing: it prints the calls that would.

Set ``BW_SERVE_URL`` to reach a ``bw serve`` somewhere other than
``http://localhost:8087``. Run it with::

    python examples/device_approval.py
"""

from __future__ import annotations

import os
import sys

from bw_serve_client import ApiClient
from bw_serve_client import DeviceApproval
from bw_serve_client import ExternalServiceError
from bw_serve_client import Organizations
from bw_serve_client import UserError
from bw_serve_client import ValidationError


def main() -> int:
  """Print each organization's pending device requests.

  Returns:
    The process exit status.
  """
  base_url = os.environ.get("BW_SERVE_URL", "http://localhost:8087")

  with ApiClient(base_url=base_url) as client:
    try:
      organizations = Organizations(client).list()

    except ExternalServiceError as error:
      print(f"Cannot reach bw serve at {base_url}: {error}", file=sys.stderr)
      return 1

    except UserError as error:
      print(f"Unlock the vault first: {error}", file=sys.stderr)
      return 1

    approvals = DeviceApproval(client)

    for organization in organizations:
      if organization.id is None:
        continue

      try:
        pending = approvals.list(organization.id)

      except ValidationError as error:
        if error.status_code == 404:
          print("This bw serve has no device approval: it needs the licensed CLI build", file=sys.stderr)
          return 1

        # A 400 here is usually the account lacking the permission to
        # manage the organization's users' passwords.
        print(f"{organization.name}: {error}")
        continue

      print(f"{organization.name}: {len(pending)} pending requests")

      for request in pending:
        print(f"  {request.email} on {request.request_device_type} from {request.request_ip_address}")
        print(f"    approvals.approve({str(organization.id)!r}, {request.id!r}) would approve it")

  return 0


if __name__ == "__main__":
  sys.exit(main())
