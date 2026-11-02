bw-serve-client
===============

A Python client for the Bitwarden `Vault Management API`_, the local HTTP
API that ``bw serve`` (the Bitwarden CLI's server) provides. Each route is
a method on a resource class; arguments are validated, and responses
parsed, with pydantic models generated from Bitwarden's OpenAPI spec.

Installing it, starting ``bw serve`` and the update pipeline are in the
`README`_; a runnable script for each resource class is in `examples`_.
This site is the API reference.

.. code-block:: python

   from bw_serve_client import ApiClient, Folders

   with ApiClient() as client:
       for folder in Folders(client).list():
           print(folder.name)

Connecting
----------

An :class:`~bw_serve_client.api_client.ApiClient` talks to a ``bw serve``
that is already running; it never starts or stops one. It reaches the
server one of three ways:

URL
   The default, ``http://localhost:8087``, which is where ``bw serve``
   listens unless started with ``--hostname`` or ``--port``. Pass
   ``protocol``, ``domain``, ``port`` and ``path``, or the whole URL as
   ``base_url``.

Unix socket
   ``base_url="unix:///path/to/bw.sock"``. Requests go over the socket
   with the header ``Host: localhost:<port>``, so ``port`` must be the
   port ``bw serve`` was started with.

Your own transport
   Any ``httpx.BaseTransport`` as ``transport``, used as it is;
   ``max_retries`` does not apply to it.

``timeout``, ``max_retries`` (connection attempts only; an error status
is never retried), ``user_agent``, ``logger`` and ``error_handler`` are
the remaining options.

Authentication
--------------

There is none in this library. ``bw serve`` has no authentication on its
endpoints: the login and the unlocked vault live in the ``bw serve``
process. Unlock the vault before starting it (``bw unlock``), or unlock it
through the API with
:meth:`VaultControl.unlock() <bw_serve_client.vault_control.VaultControl.unlock>`.

Anything that can reach the port or socket can use the unlocked vault, so
keep ``bw serve`` bound to localhost or to a socket only you can open.

Errors
------

Every failure goes to the client's error handler. By default it raises
one of the :doc:`error classes <api/errors>`: ``ValidationError``,
``UserError`` (a locked vault, for one), ``ExternalServiceError`` or
``InternalError``, all under ``BitwardenError``. Pass your own handler, or
a :class:`~bw_serve_client.errors.DefaultErrorHandler` with a different
``error_level``, to have some of them returned instead.

API reference
-------------

.. toctree::
   :maxdepth: 2

   api/api-client
   api/resources
   api/errors
   api/models

* :ref:`genindex`
* :ref:`search`

.. _Vault Management API: https://bitwarden.com/help/vault-management-api/
.. _README: https://github.com/harleypig/bw-serve-client#readme
.. _examples: https://github.com/harleypig/bw-serve-client/tree/master/examples
