Resource classes
================

One class per area of the Vault Management API, each method one route.
Every class is built on a shared client::

   from bw_serve_client import ApiClient, Folders

   with ApiClient() as client:
       folders = Folders(client)

The constructor also takes ``logger`` and ``error_handler``; either
defaults to the client's. An ``error_handler`` given here handles that
class's failures. A ``logger`` given here receives only the class's
one-line request trace: request and response records still go to the
client's logger, and errors to the error handler.

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
