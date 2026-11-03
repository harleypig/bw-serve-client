Tutorial: a script over a Unix socket
=====================================

This page builds a small script that counts the logins in each folder of
your vault. It talks to ``bw serve`` over a Unix socket instead of a TCP
port, and when something goes wrong it prints one clear line and exits
with a status a shell, cron or systemd can act on. The script is the
point; the counting is only something for it to do.

Why a socket: anything that can reach ``bw serve``'s port can use the
unlocked vault, and on a shared machine every local user can reach
``localhost``. A socket file can be made readable by you alone.

Serving on a socket needs Bitwarden CLI 2025.9.0 or later.

1. Start bw serve on a socket
-----------------------------

In a shell where ``bw`` is logged in:

.. code-block:: bash

   export BW_SESSION="$(bw unlock --raw)"
   bw serve --hostname "unix://$XDG_RUNTIME_DIR/bw.sock"

``$XDG_RUNTIME_DIR`` is a directory only you can read, such as
``/run/user/1000``; any path you control will do. Leave the server
running and use another terminal for the script.

2. The script
-------------

Save this as ``folder_report.py``:

.. code-block:: python

   """Count the logins in each folder, over bw serve's Unix socket."""

   from collections import Counter
   import os
   import sys

   from bw_serve_client import ApiClient
   from bw_serve_client import ExternalServiceError
   from bw_serve_client import Folders
   from bw_serve_client import UserError
   from bw_serve_client import ValidationError
   from bw_serve_client import VaultControl
   from bw_serve_client import VaultItems

   SOCKET = os.environ.get("BW_SERVE_SOCKET", f"{os.environ.get('XDG_RUNTIME_DIR', '/tmp')}/bw.sock")

   # The port bw serve was started with; 8087 when it had no --port.
   PORT = 8087

   LOGIN = 1


   def report(client):
     """Print each folder's name and how many logins it holds."""
     names = {folder.id: folder.name for folder in Folders(client).list()}
     counts = Counter(item.folder_id for item in VaultItems(client).list() if item.type == LOGIN)

     for folder_id, count in counts.most_common():
       print(f"{count:5}  {names.get(folder_id, 'No Folder')}")


   def main():
     """Run the report; return the exit status."""
     with ApiClient(base_url=f"unix://{SOCKET}", port=PORT, timeout=10) as client:
       try:
         status = VaultControl(client).status().status.value

         if status != "unlocked":
           print(f"The vault is {status}; unlock it and try again", file=sys.stderr)
           return 1

         report(client)

       except UserError as error:
         print(f"The vault is not usable: {error}", file=sys.stderr)
         return 1

       except ExternalServiceError as error:
         print(f"Cannot talk to bw serve on {SOCKET}: {error}", file=sys.stderr)
         return 2

       except ValidationError as error:
         print(f"bw serve refused the request: {error}", file=sys.stderr)
         return 3

     return 0


   if __name__ == "__main__":
     sys.exit(main())

Run it:

.. code-block:: bash

   python folder_report.py

and it prints one line per folder, the busiest first:

.. code-block:: text

      12  Work
       4  No Folder
       1  Banking

3. How the script connects
--------------------------

``base_url="unix://..."`` tells
:class:`~bw_serve_client.api_client.ApiClient` to send every request over
the socket. ``bw serve`` still checks each request's ``Host`` header, so
the client sends ``Host: localhost:<port>``, and ``port`` must be the one
``bw serve`` was started with: 8087 unless it was given ``--port``. A
mismatch is refused with a 403, which arrives as a ``ValidationError``
naming the ``Host`` that was sent.

``timeout=10`` gives up on a request after ten seconds rather than the
default thirty. A connection that fails is retried three times before the
error is raised; ``max_retries`` changes that.

The script never sends a password or a session key. The vault was unlocked
when ``bw serve`` started, and it stays unlocked inside that process.

4. How the script fails
-----------------------

Every error the library raises is a
:class:`~bw_serve_client.errors.BitwardenError`, and the subclass says
whose problem it is. The script turns each into an exit status:

======  ====================================================  =========================
Status  Cause                                                 Raised as
======  ====================================================  =========================
0       The report printed.                                   --
1       The vault is locked, or no one is logged in.          The status check, or
                                                              ``UserError``
2       ``bw serve`` is not running, the socket path is       ``ExternalServiceError``
        wrong, or it timed out or failed.
3       ``bw serve`` refused the request as made: a port      ``ValidationError``
        that does not match, or a bad argument.
======  ====================================================  =========================

Checking :meth:`VaultControl.status()
<bw_serve_client.vault_control.VaultControl.status>` first gives a locked
vault its own message. Without it, the first vault call would raise
``UserError`` instead, and the script would still exit 1.

The script leaves :class:`~bw_serve_client.errors.InternalError` uncaught.
That one means a bug in the library, and a traceback is the most useful
thing it can produce.

To see each failure, stop ``bw serve`` and run the script (status 2), or
start ``bw serve`` without ``BW_SESSION`` set so the vault is locked
(status 1). :doc:`troubleshooting` lists the messages you will see and what
to do about each.

5. Errors returned instead of raised
------------------------------------

In a script that checks many things, catching an exception around each
call gets long. A
:class:`~bw_serve_client.errors.DefaultErrorHandler` with
``error_level=logging.ERROR`` returns validation and user errors in place
of the result, and still raises service failures and bugs. This version
reuses ``SOCKET`` and ``PORT`` from the script:

.. code-block:: python

   import logging

   from bw_serve_client import ApiClient
   from bw_serve_client import BitwardenError
   from bw_serve_client import DefaultErrorHandler
   from bw_serve_client import Folders

   handler = DefaultErrorHandler(error_level=logging.ERROR)

   with ApiClient(base_url=f"unix://{SOCKET}", port=PORT, error_handler=handler) as client:
     folders = Folders(client).list()

     if isinstance(folders, BitwardenError):
       print("Could not list folders:", folders)

     else:
       print(len(folders), "folders")

Every method's result must then be checked with ``isinstance`` before it is
used. Pick one style per script.

Where next
----------

- :doc:`organise-items` — create a folder and a login, and move it into a
  collection.
- :doc:`troubleshooting` — what each common error means and how to fix it.
- `examples/serve_socket.py`_ — a script that starts ``bw serve`` on a
  socket itself, queries it and stops it.

.. _examples/serve_socket.py: https://github.com/harleypig/bw-serve-client/blob/master/examples/serve_socket.py
