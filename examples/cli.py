"""A small command-line app that uses the library from start to finish.

Each script beside this one shows one resource class. This one shows how
the pieces fit together: connecting, calling a few resource classes,
reading the models they return, turning each error into a message and an
exit status, and injecting a logger and an error handler.

It reads the vault and changes nothing. It never logs in, unlocks or starts
``bw serve`` either -- the library does none of those things -- so
``setup`` prints the steps to do that with ``bw`` and checks which one is
missing. Run it with::

    python examples/cli.py --help
    python examples/cli.py setup
    python examples/cli.py --url unix:///run/user/1000/bw.sock items --search github
    python examples/cli.py item <id> --show-secrets

Set ``BW_SERVE_URL`` or pass ``--url`` to reach a ``bw serve`` somewhere
other than ``http://localhost:8087``.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Any, Callable, Optional

from pydantic import SecretStr

from bw_serve_client import ApiClient
from bw_serve_client import BitwardenError
from bw_serve_client import DefaultErrorHandler
from bw_serve_client import ExternalServiceError
from bw_serve_client import Folders
from bw_serve_client import UserError
from bw_serve_client import ValidationError
from bw_serve_client import VaultControl
from bw_serve_client import VaultItems

# argparse already exits 2 for a bad command line.
EXIT_OK = 0
EXIT_NO_SERVER = 3
EXIT_LOCKED = 4
EXIT_INVALID = 5
EXIT_SERVER_ERROR = 6

SETUP_STEPS = """\
This app needs a running bw serve. Set it up with the bw CLI:

  1. Log in, once per device:
       bw login
  2. Unlock, and export the session key for bw serve:
       export BW_SESSION="$(bw unlock --raw)"
  3. Start the server, on a port or a Unix socket:
       bw serve                       # http://localhost:8087
       bw serve --hostname unix:///run/user/1000/bw.sock

Then pass --url, or set BW_SERVE_URL, if it is not at http://localhost:8087.
"""

UNLOCK_HINT = 'Unlock it with: export BW_SESSION="$(bw unlock --raw)", then restart bw serve.'


def _secret(value: Any, show: bool) -> str:
  """Render a field, revealing a ``SecretStr`` only when asked.

  Args:
    value: A model field: a ``SecretStr``, a plain value or ``None``.
    show: Whether to reveal a secret.

  Returns:
    The text to print; a hidden secret prints as asterisks.
  """
  if isinstance(value, SecretStr) and show:
    return value.get_secret_value()

  return "" if value is None else str(value)


def _raised(result: Any) -> Any:
  """Raise an error the handler returned, so one ``except`` serves both modes.

  Under ``--verbose`` the handler returns validation and user errors in
  place of a result, instead of raising them.

  Args:
    result: What a resource method returned.

  Returns:
    ``result``, when it is not an error.

  Raises:
    result: When it is a :class:`BitwardenError`.
  """
  if isinstance(result, BitwardenError):
    raise result

  return result


def cmd_status(client: ApiClient, args: argparse.Namespace) -> int:
  """Print who is logged in and whether the vault is locked.

  Args:
    client: The connected client.
    args: The parsed command line: ``url``.

  Returns:
    The exit status.
  """
  status = _raised(VaultControl(client).status())

  if status is None or status.status is None:
    print("bw serve reported no vault status", file=sys.stderr)
    return EXIT_SERVER_ERROR

  print(f"bw serve at {args.url}: {status.user_email} on {status.server_url}, {status.status.value}")

  if status.status.value == "locked":
    print(UNLOCK_HINT, file=sys.stderr)

  return EXIT_OK


def cmd_setup(client: ApiClient, args: argparse.Namespace) -> int:
  """Print the setup steps, then say which one is still missing.

  Args:
    client: The connected client.
    args: The parsed command line: ``url``.

  Returns:
    The exit status: ``EXIT_OK`` only when the vault is unlocked.
  """
  print(SETUP_STEPS)
  status = _raised(VaultControl(client).status())
  state = status.status.value if status is not None and status.status is not None else "unknown"

  if state == "unlocked":
    print(f"All set: bw serve answers at {args.url} and the vault is unlocked.")
    return EXIT_OK

  if state == "locked":
    print("Step 2 is missing: bw serve answers, but the vault is locked.", file=sys.stderr)
    return EXIT_LOCKED

  print(f"Step 1 is missing: bw serve answers, but reports the vault {state}.", file=sys.stderr)
  return EXIT_LOCKED


def cmd_folders(client: ApiClient, args: argparse.Namespace) -> int:
  """List the folders, optionally filtered by a search term.

  Args:
    client: The connected client.
    args: The parsed command line: ``search``.

  Returns:
    The exit status.
  """
  for folder in _raised(Folders(client).list(search=args.search)):
    # The "No Folder" pseudo-folder has no id.
    print(f"{str(folder.id or '-'):36}  {folder.name}")

  return EXIT_OK


def cmd_items(client: ApiClient, args: argparse.Namespace) -> int:
  """List the items, optionally filtered by a search term.

  Args:
    client: The connected client.
    args: The parsed command line: ``search``.

  Returns:
    The exit status.
  """
  for item in _raised(VaultItems(client).list(search=args.search)):
    print(f"{item.id}  {item.name}")

  return EXIT_OK


def cmd_item(client: ApiClient, args: argparse.Namespace) -> int:
  """Show one item, its secrets masked unless ``--show-secrets`` is given.

  Args:
    client: The connected client.
    args: The parsed command line: ``id`` and ``show_secrets``.

  Returns:
    The exit status.
  """
  item = _raised(VaultItems(client).get(args.id))
  show = args.show_secrets

  print(f"name:     {item.name}")
  print(f"id:       {item.id}")

  if item.login is not None:
    print(f"username: {_secret(item.login.username, show)}")
    print(f"password: {_secret(item.login.password, show)}")

    for uri in item.login.uris or []:
      print(f"uri:      {uri.uri}")

  for field in item.fields or []:
    print(f"field:    {field.name} = {_secret(field.value, show)}")

  return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
  """Describe the command line.

  Returns:
    The parser; each subcommand sets ``func`` to the function that runs it.
  """
  parser = argparse.ArgumentParser(prog="cli.py", description="Read a Bitwarden vault through a running bw serve.")
  parser.add_argument(
    "--url",
    default=os.environ.get("BW_SERVE_URL", "http://localhost:8087"),
    help="where bw serve listens: http://host:port or unix:///path/to/socket (default: $BW_SERVE_URL, else http://localhost:8087)"
  )
  parser.add_argument("-v", "--verbose", action="store_true", help="log each request and every error to stderr")

  commands = parser.add_subparsers(dest="command", required=True, metavar="command")

  commands.add_parser("setup", help="print the bw serve setup steps and check which is missing").set_defaults(func=cmd_setup)
  commands.add_parser("status", help="show the logged-in user and whether the vault is locked").set_defaults(func=cmd_status)

  folders = commands.add_parser("folders", help="list folders")
  folders.add_argument("--search", help="only folders whose name contains this")
  folders.set_defaults(func=cmd_folders)

  items = commands.add_parser("items", help="list items")
  items.add_argument("--search", help="only items whose name, username or URI contains this")
  items.set_defaults(func=cmd_items)

  item = commands.add_parser("item", help="show one item, secrets masked")
  item.add_argument("id", help="the item's id")
  item.add_argument("--show-secrets", action="store_true", help="print passwords and hidden fields in the clear")
  item.set_defaults(func=cmd_item)

  return parser


def main(argv: Optional[list[str]] = None, connect: Callable[..., ApiClient] = ApiClient) -> int:
  """Parse the command line, run one command and map its failure to an exit status.

  Args:
    argv: The arguments, without the program name; ``sys.argv[1:]`` when ``None``.
    connect: Builds the client; the tests pass one that answers from recordings.

  Returns:
    The process exit status.
  """
  args = build_parser().parse_args(argv)
  logger = None
  handler = None

  if args.verbose:
    # Both hooks are injected: the client logs requests and responses to
    # ``logger``, and the handler logs every error there too, but returns
    # validation and user errors instead of raising them (see _raised).
    logging.basicConfig(format="%(levelname)s %(name)s: %(message)s")
    logger = logging.getLogger("bw-serve-cli")
    logger.setLevel(logging.DEBUG)
    handler = DefaultErrorHandler(logger=logger, error_level=logging.ERROR)

  try:
    with connect(base_url=args.url, logger=logger, error_handler=handler) as client:
      return args.func(client, args)

  except UserError as error:
    print(f"{error}\n{UNLOCK_HINT}", file=sys.stderr)
    return EXIT_LOCKED

  except ValidationError as error:
    print(f"Request refused: {error}", file=sys.stderr)
    return EXIT_INVALID

  except ExternalServiceError as error:
    if error.status_code is not None:
      print(f"bw serve failed: {error}", file=sys.stderr)
      return EXIT_SERVER_ERROR

    print(f"Step 3 is missing: no bw serve answered at {args.url}: {error}", file=sys.stderr)

    # setup has printed the steps already.
    if args.command != "setup":
      print(f"\n{SETUP_STEPS}", file=sys.stderr)

    return EXIT_NO_SERVER


if __name__ == "__main__":
  sys.exit(main())
