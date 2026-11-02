Resource classes
================

One class per area of the Vault Management API, each method one route.
Every class is built on a shared client::

   from bw_serve_client import ApiClient, Folders

   with ApiClient() as client:
       folders = Folders(client)

The constructor also takes ``logger`` and ``error_handler``; either
defaults to the client's, so both can be set once on the
:class:`~bw_serve_client.api_client.ApiClient` and overridden per
resource.

A method validates its arguments against the generated models before it
sends anything, and parses the response into a model. When the error
handler returns instead of raising, a method returns the handler's value
in place of its result.

.. toctree::
   :maxdepth: 2

   resources/vault_items
   resources/folders
   resources/attachments
   resources/item_fields
   resources/sends
   resources/vault_control
   resources/utilities
   resources/organizations
   resources/org_collections
   resources/device_approval
