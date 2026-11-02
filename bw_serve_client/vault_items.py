"""Vault items domain class for the Bitwarden Vault Management API.

Mirrors the ``Vault Items`` tag in the API spec. One method per route::

  GET    /list/object/items      - VaultItems.list
  POST   /object/item            - VaultItems.add
  PUT    /object/item/{id}       - VaultItems.modify
  GET    /object/item/{id}       - VaultItems.get
  DELETE /object/item/{id}       - VaultItems.delete
  POST   /restore/item/{id}      - VaultItems.restore
  POST   /archive/{object}/{id}  - VaultItems.archive
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Any, get_args, Optional, Union

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from ._generated.models import ArchiveObjectIdPostParameters
from ._generated.models import ItemSchema
from ._generated.models import ItemTemplateSchema
from ._generated.models import ListObjectItemsGetParameters
from ._generated.models import ObjectItemIdDeleteParameters
from ._generated.models import ObjectItemIdGetParameters
from ._generated.models import ObjectItemIdPutParameters
from ._generated.models import RestoreItemIdPostParameters
from .errors import ValidationError
from .resource import _reveal
from .resource import ObjectId
from .resource import Resource
from .resource import route

ItemId = ObjectId

#: What ``add`` and ``modify`` take: request fields, by alias or by field
#: name, a built request model, or an item fetched from bw serve.
ItemInput = Union[ItemSchema, ItemTemplateSchema, Mapping[str, Any]]


class _SearchPath(BaseModel):
  """The path of a get by search term, in place of the item id.

  Attributes:
      id: The search term; ``Resource`` percent-encodes it into the path.
      model_config: Refuses unknown fields.
  """

  model_config = ConfigDict(extra="forbid")

  # An empty term would leave ``/object/item/``, which is not a route.
  id: Annotated[str, Field(min_length=1)]


class _DeleteQuery(BaseModel):
  """The query of a delete.

  The generated ``ObjectItemIdDeleteParameters`` holds the path ``id``
  and the query ``permanent`` in one model, so it validates the path and
  this model validates the query.

  Attributes:
      permanent: Delete permanently rather than move to the trash.
      model_config: Refuses unknown fields.
  """

  model_config = ConfigDict(extra="forbid")

  permanent: Optional[bool] = None


# -----------------------------------------------------------------------------
def _nested_model(annotation: Any) -> Optional[type[BaseModel]]:
  """Find the model a field holds, alone or in a sequence or union.

  Args:
      annotation: A model field's annotation.

  Returns:
      The model class, or ``None`` when the field holds no model.
  """
  if isinstance(annotation, type) and issubclass(annotation, BaseModel):
    return annotation

  for argument in get_args(annotation):
    if (found := _nested_model(argument)) is not None:
      return found

  return None


# -----------------------------------------------------------------------------
def _request_fields(model: type[BaseModel], data: Mapping[str, Any]) -> dict[str, Any]:
  """Keep only what ``model`` accepts, at every level of nesting.

  The response models carry what the request models forbid -- ``id`` and
  ``revisionDate`` on the item, ``passwordRevisionDate`` on its login,
  ``uriChecksum`` on a URI -- so the set is read from the request model
  rather than listed here.

  Args:
      model: The request model.
      data: A response model dumped by field name.

  Returns:
      The fields the request model has, with nested models pruned alike.
  """
  kept: dict[str, Any] = {}

  for name, value in data.items():
    field = model.model_fields.get(name)

    if field is None:
      continue

    nested = _nested_model(field.annotation)

    if nested is not None and isinstance(value, Mapping):
      kept[name] = _request_fields(nested, value)

    elif nested is not None and isinstance(value, (list, tuple)):
      kept[name] = [_request_fields(nested, entry) if isinstance(entry, Mapping) else entry for entry in value]

    else:
      kept[name] = value

  return kept


# -----------------------------------------------------------------------------
def _request_body(item: ItemInput) -> Mapping[str, Any]:
  """Turn what ``add`` or ``modify`` was given into request fields.

  Secrets are revealed, because the request model types a login's
  password and a card's number as plain strings; ``_request`` validates
  the result and sends it. Only a fetched item is pruned: unknown keys in
  a mapping are the caller's, and validation refuses them.

  Args:
      item: Request fields, a request model, or a fetched item.

  Returns:
      Fields for ``ItemTemplateSchema``.
  """
  if isinstance(item, ItemSchema):
    return _request_fields(ItemTemplateSchema, _reveal(item.model_dump(exclude_none=True)))

  if isinstance(item, ItemTemplateSchema):
    return _reveal(item.model_dump(exclude_none=True))

  return item


class VaultItems(Resource):
  """Vault item operations: logins, notes, cards, identities and the rest.

  Construction, logging and error handling are :class:`Resource`'s. Every
  method returns what the error handler returned, in place of its result,
  when a failure is handled without raising.
  """

  # ---------------------------------------------------------------------------
  @route("GET", "/list/object/items")
  def list(
    self: VaultItems,
    *,
    organization_id: Optional[ItemId] = None,
    collection_id: Optional[ItemId] = None,
    folder_id: Optional[ItemId] = None,
    url: Optional[str] = None,
    trash: bool = False,
    archived: bool = False,
    search: Optional[str] = None,
  ) -> Union[list[ItemSchema], Any]:
    """Retrieve a list of items in your vault.

    Using multiple filters will perform a logical ``OR`` operation. Using
    filters **and** search terms will perform a logical ``AND`` operation.

    ``url`` must parse as a URL and is sent normalized:
    ``https://example.com`` goes out as ``https://example.com/``. An
    empty ``search`` filters nothing. Archiving needs a premium account.

    Args:
        organization_id: Only items in this organization.
        collection_id: Only items in this collection.
        folder_id: Only items in this folder.
        url: Only items with this URL or URI.
        trash: List the items in the trash instead.
        archived: List the archived items instead.
        search: Only items whose name, username or URI contains this.

    Returns:
        The matching items as :class:`ItemSchema` (empty if none match).
    """
    # False is bw's default for both flags (list.command.ts), so a false
    # flag is left out rather than sent.
    fields = {
      "organization_id": organization_id,
      "collection_id": collection_id,
      "folderid": folder_id,
      "url": url,
      "trash": trash or None,
      "archived": archived or None,
      "search": search or None,
    }

    return self._request("GET", "/list/object/items", query=(ListObjectItemsGetParameters, fields), response_type=list[ItemSchema])

  # ---------------------------------------------------------------------------
  @route("POST", "/object/item")
  def add(self: VaultItems, item: ItemInput) -> Union[ItemSchema, Any]:
    """Add a new item to your vault.

    Indicate the item type with ``type`` and give data only in that type's
    object (``login``, ``secureNote``, ``card``, ``identity``, ``sshKey``,
    ``bankAccount``, ``driversLicense`` or ``passport``). An unknown type
    is refused before anything is sent: bw serve would crash on it, or
    store the item as a login.

    Args:
        item: The item, as ``ItemTemplateSchema`` fields (by alias or by
            field name), an ``ItemTemplateSchema``, or an item fetched
            with ``get``, whose server-side fields (``id``,
            ``revisionDate``, ``attachments`` and the like) are dropped.

    Returns:
        The created :class:`ItemSchema` with its server-assigned id.
    """
    return self._request("POST", "/object/item", body=(ItemTemplateSchema, _request_body(item)), response_type=ItemSchema)

  # ---------------------------------------------------------------------------
  @route("PUT", "/object/item/{id}")
  def modify(self: VaultItems, item_id: ItemId, item: ItemInput) -> Union[ItemSchema, Any]:
    """Edit an item in your Vault.

    **Include the full object in the request body**, not just the
    properties to edit, as the new object will replace the pre-existing
    object.

    **Exception -- ``collectionIds`` is merged, not replaced.** Any
    collection identifiers in the request body are **added** to the
    item's existing collections; this endpoint cannot **remove** an item
    from a collection. To replace an item's collection membership
    (including removing it from a collection), use ``PUT
    /object/item-collections/{id}`` instead.

    **Exception -- this endpoint cannot change an item's ownership.**
    Editing ``organizationId`` here will not move the item. To move a
    personal item to an organization, use ``POST
    /move/{itemid}/{organizationId}``. Moving an item from one
    organization to another is not supported by the API -- delete the
    item and recreate it in the target organization.

    The usual edit is get, change, modify: pass the fetched item, changed
    with ``model_copy(update=...)``, and its server-side fields are
    dropped while its secrets go out intact, and a linked custom field
    keeps its ``linkedId``.

    Args:
        item_id: Unique identifier of the item to edit.
        item: The whole item, in any form ``add`` takes.

    Returns:
        The updated :class:`ItemSchema`.
    """
    return self._request(
      "PUT",
      "/object/item/{id}",
      path_params=(ObjectItemIdPutParameters, {
        "id": item_id
      }),
      body=(ItemTemplateSchema, _request_body(item)),
      response_type=ItemSchema,
    )

  # ---------------------------------------------------------------------------
  @route("GET", "/object/item/{id}")
  def get(self: VaultItems, item_id: Optional[ItemId] = None, *, search: Optional[str] = None) -> Union[ItemSchema, Any]:
    """Retrieve an item from your vault.

    In place of an identifier you may also provide a search term, in which
    case the first matching item is returned. If the search term matches
    more than one item, the response instead contains an array of the
    matching items so you can identify the one you want.

    That last sentence is the spec's; bw serve 2026.10.1 answers an
    ambiguous search with a 400 instead, a :class:`ValidationError` whose
    message lists the matching ids. A search term is never guessed from
    ``item_id``: an id that is not a UUID is refused, not searched for.

    Args:
        item_id: Unique identifier of the item to retrieve.
        search: A search term, in place of ``item_id``; give exactly one.

    Returns:
        The :class:`ItemSchema`.
    """
    if (item_id is None) == (search is None):
      return self._fail(ValidationError, "give exactly one of item_id and search for GET /object/item/{id}")

    if search is not None:
      path_params = (_SearchPath, {"id": search})

    else:
      path_params = (ObjectItemIdGetParameters, {"id": item_id})

    return self._request("GET", "/object/item/{id}", path_params=path_params, response_type=ItemSchema)

  # ---------------------------------------------------------------------------
  @route("DELETE", "/object/item/{id}")
  def delete(self: VaultItems, item_id: ItemId, *, permanent: bool = False) -> Any:
    """Delete an item from your vault.

    By default the item moves to the trash, from where ``restore``
    brings it back.

    Args:
        item_id: Unique identifier of the item to delete.
        permanent: Delete permanently instead of moving it to the trash.

    Returns:
        ``None``, or the error handler's return value.
    """
    return self._request(
      "DELETE",
      "/object/item/{id}",
      path_params=(ObjectItemIdDeleteParameters, {
        "id": item_id
      }),
      query=(_DeleteQuery, {
        "permanent": permanent or None
      }),
    )

  # ---------------------------------------------------------------------------
  @route("POST", "/restore/item/{id}")
  def restore(self: VaultItems, item_id: ItemId) -> Any:
    """Restore a deleted or archived item.

    Depending on the item's current state, this restores the item either
    from the trash or from the archive.

    Args:
        item_id: Unique identifier of the item to restore.

    Returns:
        ``None``, or the error handler's return value.
    """
    return self._request("POST", "/restore/item/{id}", path_params=(RestoreItemIdPostParameters, {"id": item_id}))

  # ---------------------------------------------------------------------------
  @route("POST", "/archive/{object}/{id}")
  def archive(self: VaultItems, item_id: ItemId) -> Any:
    """Archive an item.

    Archived items can be restored using ``restore``. Archiving needs
    a premium account and does not apply to organization items. The route
    takes an object type, and ``item`` is the only one, so it is not a
    parameter here.

    Args:
        item_id: Unique identifier of the item to archive.

    Returns:
        ``None``, or the error handler's return value.
    """
    return self._request(
      "POST",
      "/archive/{object}/{id}",
      path_params=(ArchiveObjectIdPostParameters, {
        "object": "item",
        "id": item_id
      }),
    )
