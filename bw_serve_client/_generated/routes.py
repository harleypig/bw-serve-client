"""Every route in the Bitwarden Vault Management API spec.

Generated from the patched OpenAPI spec by ``codegen/generate.py``.
DO NOT EDIT MANUALLY.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Parameter:
  """One parameter of a route.

  Attributes:
      name: The parameter's name in the spec.
      location: Where it goes: ``path``, ``query``, ``header`` or ``cookie``.
      required: Whether the route needs it.
  """

  name: str
  location: str
  required: bool


@dataclass(frozen=True)
class Route:
  """One operation in the spec.

  Attributes:
      method: The HTTP method, upper case.
      path: The path, with ``{name}`` parameters.
      parameters: The path, query and header parameters.
      summary: The spec's summary, or an empty string.
      description: The spec's description, or an empty string.
  """

  method: str
  path: str
  parameters: Tuple[Parameter, ...]
  summary: str
  description: str


ROUTES: Tuple[Route, ...] = (
  Route(
    method='POST',
    path='/lock',
    parameters=(),
    summary='Lock your vault.',
    description=('Lock your vault. This action will destroy the session key required to authorize requests to '
                 'most endpoints.'),
  ),
  Route(
    method='POST',
    path='/unlock',
    parameters=(),
    summary='Unlock your vault.',
    description=('Unlock your vault. This action will create the session key required to authorize requests to '
                 'most endpoints.'),
  ),
  Route(
    method='POST',
    path='/object/item',
    parameters=(),
    summary='Add a new item to your vault.',
    description='Add a new login, card, secure note, or identity to your vault.',
  ),
  Route(
    method='PUT',
    path='/object/item/{id}',
    parameters=(Parameter(name='id', location='path', required=True),),
    summary='Edit an item in your Vault.',
    description=(
      'Edit an existing login, card, secure note, or identity in your Vault by specifying a unique '
      'object identifier (e.g. `3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path and the new '
      'object contents in the request body.<br><br>**Include the full object in the request body**, '
      'not just the properties to edit, as the new object will replace the pre-existing '
      'object.<br><br>**Exception &ndash; `collectionIds` is merged, not replaced.** Any collection '
      "identifiers in the request body are **added** to the item's existing collections; this "
      "endpoint cannot **remove** an item from a collection. To replace an item's collection "
      'membership (including removing it from a collection), use `PUT /object/item-collections/{id}` '
      "instead.<br><br>**Exception &ndash; this endpoint cannot change an item's ownership.** "
      'Editing `organizationId` here will not move the item. To move a personal item to an '
      'organization, use `POST /move/{itemid}/{organizationId}`. Moving an item from one '
      'organization to another is not supported by the API &ndash; delete the item and recreate it '
      'in the target organization.'
    ),
  ),
  Route(
    method='GET',
    path='/object/item/{id}',
    parameters=(Parameter(name='id', location='path', required=True),),
    summary='Retrieve an item from your vault.',
    description=(
      'Retrieve an existing item from your vault by specifying a unique object identifier (e.g. '
      '`3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path.<br><br>In place of an identifier you may '
      'also provide a search term, in which case the first matching item is returned. If the search '
      'term matches more than one item, the response instead contains an array of the matching items '
      'so you can identify the one you want.'
    ),
  ),
  Route(
    method='DELETE',
    path='/object/item/{id}',
    parameters=(
      Parameter(name='id', location='path', required=True),
      Parameter(name='permanent', location='query', required=False),
    ),
    summary='Delete an item from your vault.',
    description=(
      'Delete an existing item from your vault by specifying the unique object identifier (e.g. '
      '`3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path.'
    ),
  ),
  Route(
    method='GET',
    path='/object/item-collections/{id}',
    parameters=(Parameter(name='id', location='path', required=True),),
    summary='Retrieve the Collection IDs an item belongs to.',
    description=(
      "Retrieve the Collection membership of an item by specifying the item's unique object "
      'identifier (e.g. `3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path. Returns a '
      'template-shaped object listing the Collection identifiers the item currently belongs to.'
    ),
  ),
  Route(
    method='PUT',
    path='/object/item-collections/{id}',
    parameters=(Parameter(name='id', location='path', required=True),),
    summary='Replace the Collections an item belongs to.',
    description=(
      "Replace the Collection membership of an item by specifying the item's unique object "
      'identifier (e.g. `3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path and an array of '
      'Collection identifiers in the request body. This performs a **full replace**: the item is '
      'placed into exactly the Collections you specify, so this is the only way over the API to '
      '**remove** an item from a Collection. The item must already belong to an organization.'
    ),
  ),
  Route(
    method='POST',
    path='/restore/item/{id}',
    parameters=(Parameter(name='id', location='path', required=True),),
    summary='Restore a deleted or archived item.',
    description=(
      'Restore an item by specifying the unique object identifier (e.g. '
      "`3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path. Depending on the item's current state, "
      'this restores the item either from the trash or from the archive.'
    ),
  ),
  Route(
    method='POST',
    path='/archive/{object}/{id}',
    parameters=(
      Parameter(name='object', location='path', required=True),
      Parameter(name='id', location='path', required=True),
    ),
    summary='Archive an item.',
    description=(
      "Archive an item by specifying the object type and the item's unique object identifier (e.g. "
      '`3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path. Only `item` is supported as the object '
      'type. Archived items can be restored using `POST /restore/item/{id}`.'
    ),
  ),
  Route(
    method='GET',
    path='/list/object/items',
    parameters=(
      Parameter(name='organizationId', location='query', required=False),
      Parameter(name='collectionId', location='query', required=False),
      Parameter(name='folderid', location='query', required=False),
      Parameter(name='url', location='query', required=False),
      Parameter(name='trash', location='query', required=False),
      Parameter(name='archived', location='query', required=False),
      Parameter(name='search', location='query', required=False),
    ),
    summary='Retrieve a list of items in your vault.',
    description=(
      'Retrieve a list of existing items in your vault. By default, this will return a list of all '
      'existing items in your vault, however you can specify filters or search terms as query '
      'parameters to narrow list results.<br><br>Using multiple filters will perform a logical `OR` '
      'operation. Using filters **and** search terms will perform a logical `AND` operation.'
    ),
  ),
  Route(
    method='POST',
    path='/attachment',
    parameters=(Parameter(name='itemid', location='query', required=True),),
    summary='Attach a file to an existing vault item.',
    description=(
      "Attach a file to an existing vault item by specifying a the vault item's identifier (e.g. "
      '`3a84be8d-12e7-4223-98cd-ae0000eabdec`) as a query parameter and the file in the request body.'
    ),
  ),
  Route(
    method='GET',
    path='/object/attachment/{id}',
    parameters=(
      Parameter(name='id', location='path', required=True),
      Parameter(name='itemid', location='query', required=True),
    ),
    summary='Retrieve an attachment.',
    description=(
      'Retreive an attachment by specifying the attachment id (e.g. '
      '`o4lrz575u84koanvu9f5gqv9a9ab92gf`) in the path and item id (e.g. '
      "`ba624b21-1c8a-43b3-a713-ae0000eabdec`) as a query parameter.<br><br>If you're retrieving any "
      'file type other than plaintext, we recommend posting the request through a browser window for '
      'immediate download.'
    ),
  ),
  Route(
    method='DELETE',
    path='/object/attachment/{id}',
    parameters=(
      Parameter(name='id', location='path', required=True),
      Parameter(name='itemid', location='query', required=True),
    ),
    summary='Delete an attachment.',
    description=(
      'Delete an attachment by specifying the attachment id (e.g. '
      '`o4lrz575u84koanvu9f5gqv9a9ab92gf`) in the path and item id (e.g. '
      '`ba624b21-1c8a-43b3-a713-ae0000eabdec`) as a query parameter.'
    ),
  ),
  Route(
    method='GET',
    path='/object/username/{id}',
    parameters=(Parameter(name='id', location='path', required=True),),
    summary='Retrieve the username of a login item.',
    description=(
      "Retrieve the username of a login item by specifying the item's unique object identifier (e.g. "
      '`3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path.'
    ),
  ),
  Route(
    method='GET',
    path='/object/password/{id}',
    parameters=(Parameter(name='id', location='path', required=True),),
    summary='Retrieve the password of a login item.',
    description=(
      "Retrieve the password of a login item by specifying the item's unique object identifier (e.g. "
      '`3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path.'
    ),
  ),
  Route(
    method='GET',
    path='/object/uri/{id}',
    parameters=(Parameter(name='id', location='path', required=True),),
    summary='Retrieve the URI of a login item.',
    description=(
      "Retrieve the URI of a login item by specifying the item's unique object identifier (e.g. "
      '`3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path.'
    ),
  ),
  Route(
    method='GET',
    path='/object/totp/{id}',
    parameters=(Parameter(name='id', location='path', required=True),),
    summary='Retrieve the TOTP code of a login item.',
    description=(
      "Retrieve the TOTP code of a login item by specifying the item's unique object identifier "
      '(e.g. `3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path.'
    ),
  ),
  Route(
    method='GET',
    path='/object/notes/{id}',
    parameters=(Parameter(name='id', location='path', required=True),),
    summary='Retrieve the notes of an item.',
    description=(
      "Retrieve the notes of an item by specifying the item's unique object identifier (e.g. "
      '`3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path.'
    ),
  ),
  Route(
    method='GET',
    path='/object/exposed/{id}',
    parameters=(Parameter(name='id', location='path', required=True),),
    summary='Retrieve the number of times a password has been exposed for a login item.',
    description=(
      'Retrieve the number of times a password has been exposed for a login item by specifying the '
      "item's unique object identifier (e.g. `3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path."
    ),
  ),
  Route(
    method='POST',
    path='/object/folder',
    parameters=(),
    summary='Add a folder to your vault.',
    description='Add a folder to your vault.',
  ),
  Route(
    method='PUT',
    path='/object/folder/{id}',
    parameters=(Parameter(name='id', location='path', required=True),),
    summary='Edit a folder in your vault.',
    description=(
      'Edit an existing folder in your vault by specifying the unique folder identifier (e.g. '
      '`3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path and the new folder `"name":` in the '
      'request body.'
    ),
  ),
  Route(
    method='GET',
    path='/object/folder/{id}',
    parameters=(Parameter(name='id', location='path', required=True),),
    summary='Retrieve a folder from your vault.',
    description=(
      'Retrieve an existing folder from your vault by specifying the unique folder identifier (e.g. '
      '`3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path.'
    ),
  ),
  Route(
    method='DELETE',
    path='/object/folder/{id}',
    parameters=(Parameter(name='id', location='path', required=True),),
    summary='Delete a folder from your vault.',
    description=(
      'Delete an existing folder from your vault by specifying the unique folder identifier (e.g. '
      '`3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path.<br><br>Deleting a folder **will not** '
      'delete the items in it.'
    ),
  ),
  Route(
    method='GET',
    path='/list/object/folders',
    parameters=(Parameter(name='search', location='query', required=False),),
    summary='Retrieve a list of folders in your vault.',
    description=(
      'Retrieve a list of folders in your vault. By default, this will return a list of all folders, '
      'however you can specify search terms as query parameters to narrow list results.'
    ),
  ),
  Route(
    method='POST',
    path='/object/send',
    parameters=(),
    summary='Create a Send.',
    description='Create a Send.<br><br>**Only Text Sends are supported.**',
  ),
  Route(
    method='PUT',
    path='/object/send/{id}',
    parameters=(Parameter(name='id', location='path', required=True),),
    summary='Edit a Send.',
    description=(
      'Edit an existing Send by specifying the unique object identifier (e.g. '
      '`e813e187-70e3-4feb-950a-ae52010c4b56`) in the path and the new object contents in the '
      'request body.<br><br> **Only Text Sends are supported.**'
    ),
  ),
  Route(
    method='GET',
    path='/object/send/{id}',
    parameters=(Parameter(name='id', location='path', required=True),),
    summary='Retrieve a Send.',
    description=(
      'Retrieve a Send by specifying the unique object identifier (e.g. '
      '`e813e187-70e3-4feb-950a-ae52010c4b56`) in the path.<br><br>**Only Text Sends are supported.**'
    ),
  ),
  Route(
    method='DELETE',
    path='/object/send/{id}',
    parameters=(Parameter(name='id', location='path', required=True),),
    summary='Delete a Send.',
    description=(
      'Delete an existing Send by specifying the unique object identifier (e.g. '
      '`e813e187-70e3-4feb-950a-ae52010c4b56`) in the path.<br><br>**Only Text Sends are supported.**'
    ),
  ),
  Route(
    method='GET',
    path='/list/object/send',
    parameters=(Parameter(name='search', location='query', required=False),),
    summary='Retrieve a list of Sends.',
    description=(
      'Retrieve a list of Sends. By default, this will return a list of all Send objects, however '
      'you can specify search terms as query parameters to narrow list results.<br><br>**Only Text '
      'Sends are supported.**'
    ),
  ),
  Route(
    method='GET',
    path='/send/list',
    parameters=(Parameter(name='search', location='query', required=False),),
    summary='Retrieve a list of Sends (alias).',
    description=(
      'Retrieve a list of Sends. This is an alias for `GET /list/object/send` and behaves '
      'identically.<br><br>**Only Text Sends are supported.**'
    ),
  ),
  Route(
    method='POST',
    path='/send/{id}/remove-password',
    parameters=(Parameter(name='id', location='path', required=True),),
    summary='Remove the password from a Send.',
    description='Remove the password from a Send.<br><br>**Only Text Sends are supported.**',
  ),
  Route(
    method='POST',
    path='/move/{itemid}/{organizationId}',
    parameters=(
      Parameter(name='itemid', location='path', required=True),
      Parameter(name='organizationId', location='path', required=True),
    ),
    summary='Move an item to a Collection.',
    description=(
      'Move an item to a Collection by specifying an `itemid` and `organizationId` in the path, and '
      'specifying one or more Collection identifiers in the request body.<br><br>This endpoint only '
      'works for items that do not yet belong to an organization (personal items). To move an item '
      'from one organization to another, delete the item and recreate it in the target organization.'
    ),
  ),
  Route(
    method='POST',
    path='/object/org-collection',
    parameters=(Parameter(name='organizationId', location='query', required=True),),
    summary='Create a Collection for a specified Organization.',
    description=(
      'Create a collection for a specified Organization by specifying a unique Organization '
      'identifier as a query parameter and Collection information in the request body, including its '
      '`"name":` and an array of `"groups":` to add it to.'
    ),
  ),
  Route(
    method='PUT',
    path='/object/org-collection/{id}',
    parameters=(
      Parameter(name='id', location='path', required=True),
      Parameter(name='organizationId', location='query', required=True),
    ),
    summary='Edit a Collection in a specified Organization.',
    description=(
      'Edit an existing Collection in a specified Organization by specifying the unique collection '
      'identifier (e.g. `3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path, an Organization '
      'identifier as a query parameter, and Collection information in the request body.'
    ),
  ),
  Route(
    method='GET',
    path='/object/org-collection/{id}',
    parameters=(
      Parameter(name='id', location='path', required=True),
      Parameter(name='organizationId', location='query', required=True),
    ),
    summary='Retrieve a Collection from a specified Organization.',
    description=(
      'Retrieve an existing collection from a specified Organization by specifying the unique '
      'Collection identifier (e.g. `3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path and an '
      'Organization identifier as a query parameter .'
    ),
  ),
  Route(
    method='DELETE',
    path='/object/org-collection/{id}',
    parameters=(
      Parameter(name='id', location='path', required=True),
      Parameter(name='organizationId', location='query', required=True),
    ),
    summary='Delete a Collection from a specified Organization.',
    description=(
      'Delete an existing Collection from a specified Organization by specifying the unique '
      'Collection identifier (e.g. `3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path and an '
      'Organization identifier as a query parameter.<br><br>Deleting a Collection **will not** '
      'delete the items in it.'
    ),
  ),
  Route(
    method='GET',
    path='/list/object/org-collections',
    parameters=(
      Parameter(name='organizationId', location='query', required=True),
      Parameter(name='search', location='query', required=False),
    ),
    summary='List Collections from a specified Organization.',
    description=(
      'List existing Collections from a specified Organization by specifying an Organization '
      'idenfitier as a query parameter. Collections you do not have access to will not be '
      'listed.<br><br>By default, this will return a list of all Collections, however you can '
      'specify search terms as additional query parameters to narrow list results.'
    ),
  ),
  Route(
    method='GET',
    path='/list/object/collections',
    parameters=(Parameter(name='search', location='query', required=False),),
    summary='List Collections from all member Organizations.',
    description=(
      'List Collections from all Organizations of which you are a member. Collections you do not '
      'have access to will not be listed.<br><br>By default, this will return a list of all '
      'Collections, however you can specify search terms as query parameters to narrow list results.'
    ),
  ),
  Route(
    method='GET',
    path='/list/object/organizations',
    parameters=(Parameter(name='search', location='query', required=False),),
    summary='List Organizations of which you are a member.',
    description=(
      'List Organizations of which you are a member. By default, this will return a list of all '
      'Organizations, however you can specify search terms as query parameters to narrow list '
      'results.'
    ),
  ),
  Route(
    method='GET',
    path='/list/object/org-members',
    parameters=(Parameter(name='organizationId', location='query', required=True),),
    summary='List members of a specified Organization.',
    description=('List members of a specified Organization by specifying an Organization identifier as a query '
                 'parameter.'),
  ),
  Route(
    method='GET',
    path='/object/collection/{id}',
    parameters=(Parameter(name='id', location='path', required=True),),
    summary='Retrieve a Collection from local state.',
    description=(
      'Retrieve a single Collection synced to your local state by specifying its unique identifier '
      '(e.g. `3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path.<br><br>This is distinct from `GET '
      '/object/org-collection/{id}`, which fetches a Collection directly from the server and is '
      'restricted to certain administrative roles and the **Can Manage** permission.'
    ),
  ),
  Route(
    method='GET',
    path='/object/organization/{id}',
    parameters=(Parameter(name='id', location='path', required=True),),
    summary='Retrieve an Organization you are a member of.',
    description=(
      'Retrieve a single Organization that you are a member of from local state by specifying its '
      'unique identifier (e.g. `3c89a31d-f1cc-4673-8d5a-ae2700f9860d`) in the path.'
    ),
  ),
  Route(
    method='POST',
    path='/confirm/org-member/{id}',
    parameters=(
      Parameter(name='id', location='path', required=True),
      Parameter(name='organizationId', location='query', required=True),
    ),
    summary='Confirm a member to a specified Organization.',
    description=(
      'Confirm a member to a specified Organization by specifying a user identifier (e.g. '
      '`6b39c966-c776-4ba9-9489-ae320149af01`) in the path and the Organization identifier (e.g. '
      '`b64d6e40-adf2-4f46-b4d2-acd40147548a`) as a query parameter.'
    ),
  ),
  Route(
    method='GET',
    path='/device-approval/{organizationId}',
    parameters=(Parameter(name='organizationId', location='path', required=True),),
    summary='Retrieve a list of pending device approval requests.',
    description=('Retrieve a list of pending device approval requests by specifying an `organizationId` in the '
                 'path.'),
  ),
  Route(
    method='POST',
    path='/device-approval/{organizationId}/approve/{request-id}',
    parameters=(
      Parameter(name='organizationId', location='path', required=True),
      Parameter(name='request-id', location='path', required=True),
    ),
    summary='Approve a specific device approval request.',
    description=(
      'Approve a specific device approval request ([learn '
      'more](https://bitwarden.com/help/approve-a-trusted-device/)) by specifying an '
      '`organizationId` and specific `request-id` in the path.<br><br>Request identifiers can be '
      'retrieved using `GET /device-approval/{organizationId}`.'
    ),
  ),
  Route(
    method='POST',
    path='/device-approval/{organizationId}/approve-all',
    parameters=(Parameter(name='organizationId', location='path', required=True),),
    summary='Approve all pending device approval requests.',
    description=(
      'Approve all pending device approval requests ([learn '
      'more](https://bitwarden.com/help/approve-a-trusted-device/)) by specifying an '
      '`organizationId` in the path.'
    ),
  ),
  Route(
    method='POST',
    path='/device-approval/{organizationId}/deny/{request-id}',
    parameters=(
      Parameter(name='organizationId', location='path', required=True),
      Parameter(name='request-id', location='path', required=True),
    ),
    summary='Deny a specific device approval request.',
    description=(
      'Deny a specific device approval request [learn '
      'more](https://bitwarden.com/help/approve-a-trusted-device/)) by specifying an '
      '`organizationId` and specific `request-id` in the path.<br><br>Request identifiers can be '
      'retrieved using `GET /device-approval/{organizationId}`.'
    ),
  ),
  Route(
    method='POST',
    path='/device-approval/{organizationId}/deny-all',
    parameters=(Parameter(name='organizationId', location='path', required=True),),
    summary='Deny all pending device approval requests.',
    description=(
      'Deny all pending device approval requests ([learn '
      'more](https://bitwarden.com/help/approve-a-trusted-device/)) by specifying an '
      '`organizationId` in the path.'
    ),
  ),
  Route(
    method='POST',
    path='/sync',
    parameters=(Parameter(name='force', location='query', required=False),),
    summary='Sync your vault.',
    description='Sync your vault.',
  ),
  Route(
    method='GET',
    path='/status',
    parameters=(),
    summary='Get the status of the Bitwarden CLI.',
    description=('Get the current `serverURL`, `lastSync`, `userEmail`, `userId`, and `status` of your '
                 'Bitwarden CLI client.'),
  ),
  Route(
    method='GET',
    path='/generate',
    parameters=(
      Parameter(name='length', location='query', required=False),
      Parameter(name='uppercase', location='query', required=False),
      Parameter(name='lowercase', location='query', required=False),
      Parameter(name='number', location='query', required=False),
      Parameter(name='special', location='query', required=False),
      Parameter(name='passphrase', location='query', required=False),
      Parameter(name='words', location='query', required=False),
      Parameter(name='separator', location='query', required=False),
      Parameter(name='capitalize', location='query', required=False),
      Parameter(name='includeNumber', location='query', required=False),
      Parameter(name='minNumber', location='query', required=False),
      Parameter(name='minSpecial', location='query', required=False),
      Parameter(name='ambiguous', location='query', required=False),
    ),
    summary='Generate a password or passphrase.',
    description=(
      'Generate a password or passphrase. By default, `/generate` will generate a 14-character '
      'password with uppercase characters, lowercase characters, and numbers.'
    ),
  ),
  Route(
    method='GET',
    path='/object/template/{type}',
    parameters=(Parameter(name='type', location='path', required=True),),
    summary='Retrieve a JSON template for any object.',
    description=(
      'Retreive a JSON template for any object, including vault items, sends, folders, and more. '
      'Templates can be used to guide you in creation of new objects.'
    ),
  ),
  Route(
    method='GET',
    path='/object/fingerprint/me',
    parameters=(),
    summary='Retrieve your fingerprint phrase.',
    description=(
      'Retrieve a fingerprint phrase. By default this returns your own account fingerprint phrase. '
      "You may also supply another user's identifier (GUID) in place of `me` in the path to look up "
      "that user's fingerprint phrase via the API."
    ),
  ),
)

__all__ = ["Parameter", "Route", "ROUTES"]
