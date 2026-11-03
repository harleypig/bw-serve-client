Troubleshooting
===============

Find the message you are seeing, or the thing that is not happening, and
the entry under it says what causes it and how to fix it.

Every error the library raises is a subclass of
:class:`~bw_serve_client.errors.BitwardenError`, and ``str(error)`` is the
message shown in each heading. When the failure came with an HTTP response,
``error.status_code`` holds its status; otherwise it is ``None``.

.. contents:: On this page
   :local:
   :depth: 1

Request failed: [Errno 111] Connection refused
----------------------------------------------

Raised as :class:`~bw_serve_client.errors.ExternalServiceError`, with no
status code, after the client has retried the connection.

**Cause.** Nothing is listening where the client connects. Either
``bw serve`` is not running, or it is listening on another port or
address.

**Fix.** Start ``bw serve``, and connect to the port it was started with:

.. code-block:: python

   from bw_serve_client import ApiClient

   client = ApiClient(port=8088)  # for bw serve --port 8088

The library never starts ``bw serve`` itself. The `README`_ covers
starting it.

Request failed: [Errno 2] No such file or directory
---------------------------------------------------

Raised as :class:`~bw_serve_client.errors.ExternalServiceError` when the
client connects over a Unix socket.

**Cause.** The socket file does not exist: ``bw serve`` is not running, or
was started with a different ``--hostname unix://...`` path.

**Fix.** Pass the exact path ``bw serve`` was given, after ``unix://``.
For ``bw serve --hostname unix:///run/user/1000/bw.sock``:

.. code-block:: python

   from bw_serve_client import ApiClient

   client = ApiClient(base_url="unix:///run/user/1000/bw.sock")

Forbidden: bw serve accepts only Host localhost, 127.0.0.1 or [::1] ...
-----------------------------------------------------------------------

Raised as :class:`~bw_serve_client.errors.ValidationError`, status code
403. The full message ends with the ``Host`` header the request carried,
such as ``this request sent Host 'myhost:8087'``.

**Cause.** ``bw serve`` refuses any request whose ``Host`` header is not
``localhost``, ``127.0.0.1``, ``[::1]`` or the ``--hostname`` it was
started with, at the port it listens on. It also refuses any request that
carries an ``Origin`` header. The client builds ``Host`` from the address
you connect to, so a machine name, a LAN address, or a port that does not
match is refused even though the connection itself worked.

**Fix.** Connect by one of those names and the port ``bw serve`` listens
on. Over a Unix socket the client sends ``Host: localhost:<port>``, taken
from ``ApiClient``'s ``port``, so pass the same ``port`` that ``bw serve``
was started with:

.. code-block:: python

   from bw_serve_client import ApiClient

   # bw serve --hostname unix:///run/user/1000/bw.sock --port 9000
   client = ApiClient(base_url="unix:///run/user/1000/bw.sock", port=9000)

The library adds no ``Origin`` header. If one is reaching ``bw serve``, a
proxy or a custom ``transport`` put it there.

Invalid URL: Invalid port: ':1:8087'
------------------------------------

Raised as :class:`~bw_serve_client.errors.ValidationError`, with no status
code, before anything is sent.

**Cause.** An IPv6 address written into a URL without brackets, such as
``base_url="http://::1:8087"``. In a URL, the colons of an IPv6 address
cannot be told apart from the one before the port.

**Fix.** Bracket the address in a URL, or pass it as ``domain``, which
brackets a bare IPv6 address for you:

.. code-block:: python

   from bw_serve_client import ApiClient

   client = ApiClient(base_url="http://[::1]:8087")
   client = ApiClient(domain="::1")  # the same URL

Vault is locked.
----------------

Raised as :class:`~bw_serve_client.errors.UserError`, status code 400, by
every call that reads or writes the vault.

**Cause.** ``bw serve`` is running, but its vault is locked. Either it was
started without a session key, or something locked it since:
``bw lock``, ``bw logout``, or
:meth:`VaultControl.lock() <bw_serve_client.vault_control.VaultControl.lock>`.

**Fix.** Restart ``bw serve`` from a shell with a fresh session key:

.. code-block:: bash

   export BW_SESSION="$(bw unlock --raw)"
   bw serve

or unlock the running server over HTTP:

.. code-block:: python

   import getpass

   from bw_serve_client import ApiClient
   from bw_serve_client import VaultControl

   with ApiClient() as client:
     VaultControl(client).unlock(getpass.getpass("Master password: "))

:meth:`VaultControl.status()
<bw_serve_client.vault_control.VaultControl.status>` works on a locked
vault, so a program can check before it starts:
``VaultControl(client).status().status.value`` is ``"unlocked"``,
``"locked"`` or ``"unauthenticated"``.

The vault is locked even though BW_SESSION is set
-------------------------------------------------

The same ``UserError: Vault is locked.`` as above, from a ``bw serve``
started with ``BW_SESSION`` exported.

**Cause.** The session key is stale or never reached the server. A key
stops working after ``bw lock``, ``bw logout`` or
:meth:`VaultControl.lock() <bw_serve_client.vault_control.VaultControl.lock>`,
and a key exported in one shell is not set in another. ``bw serve`` reads
``BW_SESSION`` from the shell that starts it.

**Fix.** Run ``bw unlock --raw`` again, export the new key, and restart
``bw serve`` from that same shell, as in the previous entry. If ``bw
status`` reports ``unauthenticated``, run ``bw login`` first.

Cryptography error, The decryption operation failed
---------------------------------------------------

Raised as :class:`~bw_serve_client.errors.UserError`, status code 400,
from :meth:`VaultControl.unlock()
<bw_serve_client.vault_control.VaultControl.unlock>`.

**Cause.** The master password was wrong.

**Fix.** Call ``unlock()`` again with the right one. The vault stays locked
until you do.

Passwords and hidden fields print as **********
-----------------------------------------------

Not an error: secrets come back as pydantic ``SecretStr`` values, which
show as ``**********`` in a ``print``, a ``repr``, a log record and an
error message. That covers a login's ``password`` and ``totp``, the value
of a hidden custom field (``type`` 1), and the session key
``unlock()`` returns.

**Fix.** Call ``get_secret_value()`` where you need the value itself:

.. code-block:: python

   from bw_serve_client import ApiClient
   from bw_serve_client import VaultItems

   with ApiClient() as client:
     item = VaultItems(client).get(search="example.com")
     password = item.login.password.get_secret_value()

A custom field's ``value`` is a ``SecretStr`` only when the field is
hidden; text, boolean and linked fields hold a plain ``str``. Check which
you have before calling ``get_secret_value()``:

.. code-block:: python

   from pydantic import SecretStr

   for field in item.fields or []:
     value = field.value.get_secret_value() if isinstance(field.value, SecretStr) else field.value

You do not need to reveal a secret to send it back. Pass the fetched item,
changed with ``model_copy(update=...)``, to
:meth:`VaultItems.modify() <bw_serve_client.vault_items.VaultItems.modify>`,
and its secrets go out intact.

A change I just made does not show up
-------------------------------------

Not an error: a list or a get straight after an add, an edit or a delete
returns what was there before.

**Cause.** ``bw serve`` can answer a read with data from before your last
write.

**Fix.** Call :meth:`VaultControl.sync()
<bw_serve_client.vault_control.VaultControl.sync>` between writing
something and reading it back.

More than one result was found
------------------------------

Raised as :class:`~bw_serve_client.errors.ValidationError`, status code
400, from ``VaultItems.get(search=...)``. The message lists the ids of the
items that matched.

**Cause.** The search term matched more than one item, and ``get`` returns
only one.

**Fix.** Use a term that matches one item, or get the item by one of the
listed ids. To see every match, use
:meth:`VaultItems.list(search=...) <bw_serve_client.vault_items.VaultItems.list>`
instead.

Not found.
----------

Raised as :class:`~bw_serve_client.errors.ValidationError`, status code
400, from a call that names an object by its id, such as ``get`` or
``archive``.

**Cause.** The id names nothing: the object was deleted, or never existed.

**Fix.** List the objects to find the current id. An item deleted without
``permanent=True`` is in the trash: ``VaultItems(client).list(trash=True)``
finds it, and :meth:`VaultItems.restore()
<bw_serve_client.vault_items.VaultItems.restore>` brings it back.

A method returned an error instead of raising it
------------------------------------------------

**Cause.** The client was built with ``DefaultErrorHandler(
error_level=logging.ERROR)``, or with your own error handler. With that
level, validation and user errors are returned in place of the result;
service failures and bugs still raise.

**Fix.** Check each result before using it, or drop the ``error_handler``
argument to have every error raise:

.. code-block:: python

   import logging

   from bw_serve_client import ApiClient
   from bw_serve_client import BitwardenError
   from bw_serve_client import DefaultErrorHandler
   from bw_serve_client import Folders

   handler = DefaultErrorHandler(error_level=logging.ERROR)

   with ApiClient(error_handler=handler) as client:
     folders = Folders(client).list()

     if isinstance(folders, BitwardenError):
       print("Could not list folders:", folders)

Still stuck
-----------

Turn on debug logging to see each request the client sends and the status
that came back. Request bodies are logged by field name only, so no secret
reaches the log:

.. code-block:: python

   import logging

   logging.basicConfig(level=logging.DEBUG)

Then `open an issue`_ with the message, the status code, and the output of
``bw --version``.

.. _README: https://github.com/harleypig/bw-serve-client#starting-bw-serve
.. _open an issue: https://github.com/harleypig/bw-serve-client/issues/new/choose
