"""Start ``bw serve`` on a Unix socket, ask it one thing, and stop it.

A minimal sketch of the part the library leaves to its caller: it talks to
a running ``bw serve`` and never starts one. Serving on a socket needs bw
CLI 2025.9.0 or later.

``bw`` must be on ``PATH`` and logged in, with ``BW_SESSION`` set so the
server starts with the vault unlocked. If it is not set, unlock first::

    export BW_SESSION="$(bw unlock --raw --passwordenv BW_PASSWORD)"

This script never sees the master password. Run it with::

    python examples/serve_socket.py
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from bw_serve_client import ApiClient
from bw_serve_client import BitwardenError
from bw_serve_client import VaultControl

MINIMUM_CLI = (2025, 9, 0)

# Over a socket ApiClient sends ``Host: localhost:<port>``, from its own
# ``port``. Recent bw CLIs answer 403 to any Host but ``localhost:`` plus
# the ``--port`` bw serve started with, even on a socket, so one constant
# feeds both.
PORT = 8087

READY_TIMEOUT = 60
STOP_TIMEOUT = 10


def cli_problem() -> str | None:
  """Check that the bw CLI on ``PATH`` can serve on a socket.

  Returns:
    Why it cannot, or None when it can.
  """
  try:
    output = subprocess.run(["bw", "--version"], capture_output=True, text=True, check=True, timeout=30).stdout
    version = tuple(int(part) for part in output.strip().split("."))

  except FileNotFoundError:
    return "bw is not on PATH; install the Bitwarden CLI first"

  except (subprocess.SubprocessError, ValueError) as error:
    return f"Could not read the bw CLI version: {error}"

  if version < MINIMUM_CLI:
    found, needed = ".".join(map(str, version)), ".".join(map(str, MINIMUM_CLI))
    return f"bw {found} cannot serve on a socket; {needed} or later is needed"

  return None


def wait_for_socket(server: subprocess.Popen[bytes], socket_path: Path) -> bool:
  """Wait until bw serve has created its socket.

  bw serve listens only once its routes are in place, so the socket
  appearing means it is ready to answer.

  Args:
    server: The running ``bw serve``.
    socket_path: Where it was told to listen.

  Returns:
    False if the server exited, or the socket did not appear in time.
  """
  deadline = time.monotonic() + READY_TIMEOUT

  while time.monotonic() < deadline:
    if server.poll() is not None:
      return False

    if socket_path.is_socket():
      return True

    time.sleep(0.2)

  return False


def stop(server: subprocess.Popen[bytes]) -> None:
  """Stop bw serve, killing it if it ignores the polite request.

  Args:
    server: The ``bw serve`` process.
  """
  server.terminate()

  try:
    server.wait(timeout=STOP_TIMEOUT)

  except subprocess.TimeoutExpired:
    server.kill()
    server.wait()


def serve_and_ask() -> int:
  """Serve on a private socket, report the vault's state, then shut down.

  Returns:
    The process exit status.
  """
  # Anyone who can connect to the socket can read the unlocked vault, so it
  # lives in a directory only this user can enter; the directory's removal
  # also clears the socket file a stopped server leaves behind.
  with tempfile.TemporaryDirectory(prefix="bw-serve-") as directory:
    socket_path = Path(directory) / "bw.sock"
    server = subprocess.Popen(["bw", "serve", "--hostname", f"unix://{socket_path}", "--port", str(PORT)])

    try:
      if not wait_for_socket(server, socket_path):
        print(f"bw serve did not start listening on {socket_path}", file=sys.stderr)
        return 1

      with ApiClient(base_url=f"unix://{socket_path}", port=PORT) as client:
        status = VaultControl(client).status()

      if status is None or status.status is None:
        print("bw serve reported no vault status", file=sys.stderr)
        return 1

      print(f"bw serve on {socket_path}: {status.user_email} is {status.status.value}")

    except BitwardenError as error:
      print(f"bw serve failed: {error}", file=sys.stderr)
      return 1

    finally:
      stop(server)

  return 0


def main() -> int:
  """Check the CLI, then run bw serve for one request.

  Returns:
    The process exit status: 130 when interrupted, as a shell reports it.
  """
  try:
    problem = cli_problem()

    if problem is not None:
      print(problem, file=sys.stderr)
      return 1

    if not os.environ.get("BW_SESSION"):
      print("BW_SESSION is not set, so bw serve starts with the vault locked", file=sys.stderr)

    return serve_and_ask()

  except KeyboardInterrupt:
    print("Interrupted", file=sys.stderr)
    return 130


if __name__ == "__main__":
  sys.exit(main())
