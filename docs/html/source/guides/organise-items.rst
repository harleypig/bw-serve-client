Tutorial: create and organise items
===================================

By the end of this page you will have created a folder, saved a login in it
with a hidden custom field, read the login back without its secrets
leaking into your output, and moved it into an organization's collection.
Each step adds to the one before, so the snippets run in order as one
script.

You need a running ``bw serve`` with the vault unlocked, on
``localhost:8087``. The `README`_ covers logging in, unlocking and starting
the server. For the last step you also need to be a member of an
organization that has a collection you can add items to; without one,
stop after step 4.

The names used here start with ``Tutorial:``, so anything the script
leaves behind is easy to find and delete.

1. Connect and check the vault
------------------------------

.. code-block:: python

   from bw_serve_client import ApiClient
   from bw_serve_client import Folders
   from bw_serve_client import OrgCollections
   from bw_serve_client import VaultControl
   from bw_serve_client import VaultItems

   client = ApiClient()  # http://localhost:8087
   vault = VaultControl(client)

   print("The vault is", vault.status().status.value)

``ApiClient()`` with no arguments connects to ``http://localhost:8087``.
The script closes it at the end; in your own code a ``with ApiClient() as
client:`` block does that for you.

The status should be ``unlocked``. If it says ``locked``, every other call
on this page raises :class:`~bw_serve_client.errors.UserError`; see
:doc:`troubleshooting`.

2. Create a folder
------------------

.. code-block:: python

   folders = Folders(client)
   folder = folders.add("Tutorial: web logins")

   print("Created folder", folder.name, "with id", folder.id)

:meth:`Folders.add() <bw_serve_client.folders.Folders.add>` returns the new
:class:`~bw_serve_client.folders.Folder`, id included. You need that id in
the next step.

3. Add a login with a hidden custom field
-----------------------------------------

An item is described by the same fields the Bitwarden CLI uses: ``type`` 1
is a login, and its username, password and URIs go under ``login``. Custom
fields go in ``fields``, each with a ``type``: 0 is text and 1 is hidden.

.. code-block:: python

   items = VaultItems(client)

   login = items.add({
     "type": 1,
     "name": "Tutorial: example.com",
     "folderId": folder.id,
     "login": {
       "username": "someone@example.com",
       "password": "correct horse battery staple",
       "uris": [{"uri": "https://example.com/"}],
     },
     "fields": [
       {"name": "Recovery code", "value": "TUTORIAL-1234-5678", "type": 1},
       {"name": "Plan", "value": "basic", "type": 0},
     ],
   })

   print("Added", login.name, "with id", login.id)

The dictionary is checked against the item model before anything is sent,
so a misspelt key or an unknown ``type`` raises
:class:`~bw_serve_client.errors.ValidationError` here instead of reaching
``bw serve``. A field name can be given as the CLI spells it
(``folderId``) or in Python style (``folder_id``).

4. Read it back
---------------

.. code-block:: python

   vault.sync()

   saved = items.get(login.id)

   print("Password:", saved.login.password)

   for field in saved.fields or []:
     print(f"{field.name}: {field.value}")

   in_folder = items.list(folder_id=folder.id)
   print(len(in_folder), "item(s) in", folder.name)

The output looks like this:

.. code-block:: text

   Password: **********
   Recovery code: **********
   Plan: basic
   1 item(s) in Tutorial: web logins

``bw serve`` can answer a read with data from before your last write, so
:meth:`VaultControl.sync() <bw_serve_client.vault_control.VaultControl.sync>`
comes first.

The password and the hidden field print as asterisks because they are
pydantic ``SecretStr`` values. They stay masked in a ``print``, a log
record and an error message. When you do need the value, ask for it:

.. code-block:: python

   password = saved.login.password.get_secret_value()

A text field's ``value`` is a plain ``str`` and a hidden field's is a
``SecretStr``, so code that reads every field checks which it has:
``field.value.get_secret_value() if isinstance(field.value, SecretStr) else
field.value``, with ``SecretStr`` imported from ``pydantic``.

5. Move it into a collection
----------------------------

Set ``COLLECTION`` to the name of a collection you can add items to.

.. code-block:: python

   COLLECTION = "Tutorial collection"

   org_collections = OrgCollections(client)
   matches = org_collections.list_collections(search=COLLECTION)

   if not matches:
     print("No collection named", COLLECTION)

   else:
     target = matches[0]
     moved = org_collections.move(saved.id, target.organization_id, [target.id])

     print("Moved to organization", moved.organization_id)
     print("Collections:", moved.collection_ids)

:meth:`OrgCollections.list_collections()
<bw_serve_client.org_collections.OrgCollections.list_collections>` reads
the vault as of its last sync and lists every collection you can reach, in
every organization; each one carries its ``organization_id``.
:meth:`OrgCollections.move()
<bw_serve_client.org_collections.OrgCollections.move>` takes the item, the
organization and one or more of its collections, and returns the item with
both set.

.. warning::

   Moving is one-way. The organization now owns the item, and the API has
   no route to move it back to your personal vault or on to another
   organization; to do either, delete the item and create it again where
   you want it.

Once an item belongs to an organization,
:meth:`OrgCollections.modify_item_collections()
<bw_serve_client.org_collections.OrgCollections.modify_item_collections>`
replaces the set of collections it is in. Editing ``collectionIds`` with
:meth:`VaultItems.modify() <bw_serve_client.vault_items.VaultItems.modify>`
only ever adds to it.

6. Clean up
-----------

.. code-block:: python

   items.delete(saved.id, permanent=True)
   folders.delete(folder.id)
   client.close()

   print("Deleted the tutorial item and folder")

Without ``permanent=True`` the item goes to the trash, from where
:meth:`VaultItems.restore() <bw_serve_client.vault_items.VaultItems.restore>`
brings it back. Deleting a folder never deletes its items; ``bw serve``
moves them to "No Folder".

The item now belongs to the organization, so the organization's
permissions decide whether you may delete it. If ``bw serve`` refuses, the
call raises :class:`~bw_serve_client.errors.ValidationError` with its
message.

Where next
----------

- :doc:`script-over-socket` — a script that runs unattended and reports
  failures through its exit status.
- :doc:`troubleshooting` — what each common error means and how to fix it.
- The `examples`_ directory — one runnable script per resource class.

.. _README: https://github.com/harleypig/bw-serve-client#starting-bw-serve
.. _examples: https://github.com/harleypig/bw-serve-client/tree/master/examples
