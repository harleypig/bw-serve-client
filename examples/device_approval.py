"""List the pending trusted-device requests of each organization.

Device approval needs both a CLI build that has the routes and a server
that implements them. A ``bw serve`` without the routes answers 404; one
with them, in front of a server without the endpoint (Vaultwarden is
one), answers 400 with the server's 404 in its message. This script
reports either and exits 1.

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
from typing import Optional

from bw_serve_client import ApiClient
from bw_serve_client import DeviceApproval
from bw_serve_client import ExternalServiceError
from bw_serve_client import Organizations
from bw_serve_client import UserError
from bw_serve_client import ValidationError


# -----------------------------------------------------------------------------
def _unavailable(error: ValidationError) -> Optional[str]:
  """Say why device approval cannot work here, if that is what failed.

  Args:
    error: What listing an organization's requests raised.

  Returns:
    The reason, or ``None`` for any other failure.
  """
  if error.status_code == 404:
    return "This bw serve has no device approval routes: its CLI build lacks them"

  # bw serve relays a server error as a 400 whose message is the server's
  # response, statusCode included, as JSON.
  if '"statusCode":404' in str(error):
    return "The server behind this bw serve does not implement device approval"

  return None


# -----------------------------------------------------------------------------
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
      print(f"bw serve at {base_url} failed: {error}", file=sys.stderr)
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
        reason = _unavailable(error)

        if reason is not None:
          print(reason, file=sys.stderr)
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
