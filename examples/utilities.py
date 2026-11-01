"""Generate a password and a passphrase, and read a template and the fingerprint.

The vault must already be unlocked for the template and the fingerprint:
start ``bw serve`` from a session where ``bw unlock`` has run. Generating
works either way.

Set ``BW_SERVE_URL`` to reach a ``bw serve`` somewhere other than
``http://localhost:8087``. Run it with::

    python examples/utilities.py
"""

from __future__ import annotations

import os
import sys

from bw_serve_client import ApiClient
from bw_serve_client import ExternalServiceError
from bw_serve_client import UserError
from bw_serve_client import Utilities


def main() -> int:
  """Use each utility once.

  Returns:
    The process exit status.
  """
  base_url = os.environ.get("BW_SERVE_URL", "http://localhost:8087")

  with ApiClient(base_url=base_url) as client:
    utilities = Utilities(client)

    try:
      password = utilities.generate(length=24, special=True, uppercase=True, lowercase=True, number=True, avoid_ambiguous=True)

    except ExternalServiceError as error:
      print(f"Cannot reach bw serve at {base_url}: {error}", file=sys.stderr)
      return 1

    # A generated password is a SecretStr: printed, it shows asterisks.
    # get_secret_value() is the deliberate step that reveals it.
    print(f"Generated a password: {password}")

    passphrase = utilities.generate(passphrase=True, words=5, separator="-", capitalize=True)
    print(f"Generated a passphrase: {passphrase}")

    try:
      print(f"The folder template: {utilities.template('folder')}")
      print(f"Your fingerprint phrase: {utilities.fingerprint()}")

    except UserError as error:
      print(f"Unlock the vault for templates and the fingerprint: {error}", file=sys.stderr)
      return 1

  return 0


if __name__ == "__main__":
  sys.exit(main())
