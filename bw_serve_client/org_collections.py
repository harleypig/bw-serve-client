"""OrgCollections domain class for the Bitwarden Vault Management API.

Mirrors the collection half of the ``Collections & Organizations`` tag in
the API spec, plus the one ``Vault Items`` route that sets an item's
collections. One ``OrgCollections`` method per route:

  POST   /object/org-collection          - add
  PUT    /object/org-collection/{id}     - modify
  GET    /object/org-collection/{id}     - get
  DELETE /object/org-collection/{id}     - delete
  GET    /object/collection/{id}         - get_collection
  POST   /move/{itemid}/{organizationId} - move
  PUT    /object/item-collections/{id}   - modify_item_collections
  GET    /list/object/collections        - list_collections
  GET    /list/object/org-collections    - list

``GET /object/item-collections/{id}`` is documented, but bw serve answers
it with a 400, so it is not offered; an item's ``collection_ids`` carries
the same list.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Optional, Union
from uuid import UUID

from ._generated.models import CollectionResponseSchema
from ._generated.models import CollectionSchema
from ._generated.models import GroupSchema
from ._generated.models import ItemSchema
from ._generated.models import ListObjectCollectionsGetParameters
from ._generated.models import ListObjectOrgCollectionsGetParameters
from ._generated.models import MoveItemidOrganizationIdPostParameters
from ._generated.models import MoveItemRequestSchema
from ._generated.models import ObjectCollectionIdGetParameters
from ._generated.models import ObjectItemCollectionsIdPutParameters
from ._generated.models import ObjectItemCollectionsIdPutRequest
from ._generated.models import ObjectOrgCollectionIdDeleteParameters
from ._generated.models import ObjectOrgCollectionIdGetParameters
from ._generated.models import ObjectOrgCollectionIdPutParameters
from ._generated.models import ObjectOrgCollectionPostParameters
from ._generated.models import OrgCollectionSchema
from .resource import Resource
from .resource import route

CollectionId = Union[UUID, str]
OrganizationId = Union[UUID, str]
ItemId = Union[UUID, str]

#: A group's or user's access to a collection: a :class:`GroupSchema`, or
#: a mapping of its fields (``id``, ``readOnly``, ``hidePasswords``,
#: ``manage``).
CollectionAccess = Union[GroupSchema, Mapping[str, Any]]

# The generated org-collection models hold the path id and the
# organizationId query in one model, so they validate the path and this
# model, which holds only organizationId, validates the query.
_OrganizationQuery = ObjectOrgCollectionPostParameters


class OrgCollections(Resource):
  """Organization collections, and putting vault items into them.

  Two families of route read collections. ``get()`` and ``list()``
  go to the server, need administrative rights in the organization or
  the **Can Manage** permission, and return groups and users.
  ``get_collection()`` and ``list_collections()`` read the vault's
  local state, as of its last sync, and see every collection the account
  can access, in every organization.

  Construction, logging and error handling are :class:`Resource`'s. Every
  method returns what the error handler returned, in place of its result,
  when a failure is handled without raising.
  """

  # ---------------------------------------------------------------------------
  @staticmethod
  def _collection_body(
    organization_id: OrganizationId,
    name: str,
    external_id: Optional[str],
    groups: Optional[Sequence[CollectionAccess]],
    users: Optional[Sequence[CollectionAccess]],
  ) -> tuple[type[CollectionSchema], dict[str, Any]]:
    """Build the org-collection request body and its model.

    bw serve refuses a body whose ``organizationId`` differs from the
    query's, so both are set from the one argument.

    Args:
        organization_id: The organization the collection is in.
        name: The collection's name.
        external_id: An identifier for the collection outside Bitwarden.
        groups: Access for groups; left out when ``None``.
        users: Access for users; left out when ``None``.

    Returns:
        The body's model and fields, for ``Resource._request``.
    """
    return (
      CollectionSchema, {
        "organizationId": organization_id,
        "name": name,
        "externalId": external_id,
        "groups": groups,
        "users": users,
      }
    )

  # ---------------------------------------------------------------------------
  @route("POST", "/object/org-collection")
  def add(
    self: OrgCollections,
    organization_id: OrganizationId,
    name: str,
    *,
    external_id: Optional[str] = None,
    groups: Optional[Sequence[CollectionAccess]] = None,
    users: Optional[Sequence[CollectionAccess]] = None,
  ) -> Union[OrgCollectionSchema, Any]:
    """Create a Collection for a specified Organization.

    Args:
        organization_id: Unique identifier of the organization.
        name: Name of the collection.
        external_id: An identifier for the collection outside Bitwarden.
        groups: Groups to give access to the collection.
        users: Users to give access to the collection.

    Returns:
        The created :class:`OrgCollectionSchema`, with its id.
    """
    return self._request(
      "POST",
      "/object/org-collection",
      query=(ObjectOrgCollectionPostParameters, {
        "organizationId": organization_id
      }),
      body=self._collection_body(organization_id, name, external_id, groups, users),
      response_type=OrgCollectionSchema,
    )

  # ---------------------------------------------------------------------------
  @route("PUT", "/object/org-collection/{id}")
  def modify(
    self: OrgCollections,
    collection_id: CollectionId,
    organization_id: OrganizationId,
    name: str,
    *,
    external_id: Optional[str] = None,
    groups: Optional[Sequence[CollectionAccess]] = None,
    users: Optional[Sequence[CollectionAccess]] = None,
  ) -> Union[OrgCollectionSchema, Any]:
    """Edit a Collection in a specified Organization.

    Args:
        collection_id: Unique identifier of the collection.
        organization_id: Unique identifier of the organization.
        name: New name of the collection.
        external_id: An identifier for the collection outside Bitwarden.
        groups: Groups to give access to the collection.
        users: Users to give access to the collection.

    Returns:
        The edited :class:`OrgCollectionSchema`.
    """
    return self._request(
      "PUT",
      "/object/org-collection/{id}",
      path_params=(ObjectOrgCollectionIdPutParameters, {
        "id": collection_id,
        "organizationId": organization_id
      }),
      query=(_OrganizationQuery, {
        "organizationId": organization_id
      }),
      body=self._collection_body(organization_id, name, external_id, groups, users),
      response_type=OrgCollectionSchema,
    )

  # ---------------------------------------------------------------------------
  @route("GET", "/object/org-collection/{id}")
  def get(self: OrgCollections, collection_id: CollectionId, organization_id: OrganizationId) -> Union[OrgCollectionSchema, Any]:
    """Retrieve a Collection from a specified Organization.

    Args:
        collection_id: Unique identifier of the collection.
        organization_id: Unique identifier of the organization.

    Returns:
        The :class:`OrgCollectionSchema`, with its groups and users.
    """
    return self._request(
      "GET",
      "/object/org-collection/{id}",
      path_params=(ObjectOrgCollectionIdGetParameters, {
        "id": collection_id,
        "organizationId": organization_id
      }),
      query=(_OrganizationQuery, {
        "organizationId": organization_id
      }),
      response_type=OrgCollectionSchema,
    )

  # ---------------------------------------------------------------------------
  @route("DELETE", "/object/org-collection/{id}")
  def delete(self: OrgCollections, collection_id: CollectionId, organization_id: OrganizationId) -> Any:
    """Delete a Collection from a specified Organization.

    Deleting a Collection **will not** delete the items in it.

    Args:
        collection_id: Unique identifier of the collection.
        organization_id: Unique identifier of the organization.

    Returns:
        ``None``, or the error handler's return value.
    """
    return self._request(
      "DELETE",
      "/object/org-collection/{id}",
      path_params=(ObjectOrgCollectionIdDeleteParameters, {
        "id": collection_id,
        "organizationId": organization_id
      }),
      query=(_OrganizationQuery, {
        "organizationId": organization_id
      }),
    )

  # ---------------------------------------------------------------------------
  @route("GET", "/object/collection/{id}")
  def get_collection(self: OrgCollections, collection_id: CollectionId) -> Union[CollectionResponseSchema, Any]:
    """Retrieve a Collection from local state.

    This is distinct from ``GET /object/org-collection/{id}``, which
    fetches a Collection directly from the server and is restricted to
    certain administrative roles and the **Can Manage** permission.

    Args:
        collection_id: Unique identifier of the collection.

    Returns:
        The :class:`CollectionResponseSchema`.
    """
    return self._request(
      "GET",
      "/object/collection/{id}",
      path_params=(ObjectCollectionIdGetParameters, {
        "id": collection_id
      }),
      response_type=CollectionResponseSchema,
    )

  # ---------------------------------------------------------------------------
  @route("POST", "/move/{itemid}/{organizationId}")
  def move(self: OrgCollections, item_id: ItemId, organization_id: OrganizationId,
           collection_ids: Sequence[CollectionId]) -> Union[ItemSchema, Any]:
    """Move an item to a Collection.

    This endpoint only works for items that do not yet belong to an
    organization (personal items). To move an item from one organization
    to another, delete the item and recreate it in the target
    organization.

    Args:
        item_id: Unique identifier of the personal item to move.
        organization_id: Unique identifier of the organization to move it to.
        collection_ids: One or more of that organization's collections.

    Returns:
        The moved item, as :class:`ItemSchema`, with its
        ``organization_id`` and ``collection_ids`` set.
    """
    return self._request(
      "POST",
      "/move/{itemid}/{organizationId}",
      path_params=(MoveItemidOrganizationIdPostParameters, {
        "itemid": item_id,
        "organizationId": organization_id
      }),
      body=(MoveItemRequestSchema, collection_ids),
      response_type=ItemSchema,
    )

  # ---------------------------------------------------------------------------
  @route("PUT", "/object/item-collections/{id}")
  def modify_item_collections(self: OrgCollections, item_id: ItemId,
                              collection_ids: Sequence[CollectionId]) -> Union[ItemSchema, Any]:
    """Replace the Collections an item belongs to.

    A full replace: the item ends up in exactly the collections given, so
    this is the only way to take an item out of a collection. The item
    must already belong to an organization; ``move()`` puts a personal
    one there.

    Args:
        item_id: Unique identifier of the item.
        collection_ids: All the collections the item is to belong to.

    Returns:
        The item, as :class:`ItemSchema`, with its new ``collection_ids``.
    """
    return self._request(
      "PUT",
      "/object/item-collections/{id}",
      path_params=(ObjectItemCollectionsIdPutParameters, {
        "id": item_id
      }),
      body=(ObjectItemCollectionsIdPutRequest, collection_ids),
      response_type=ItemSchema,
    )

  # ---------------------------------------------------------------------------
  @route("GET", "/list/object/collections")
  def list_collections(self: OrgCollections, search: Optional[str] = None) -> Union[list[CollectionResponseSchema], Any]:
    """List Collections from all member Organizations.

    Collections you do not have access to will not be listed.

    By default, this will return a list of all Collections, however you
    can specify search terms as query parameters to narrow list results.

    Args:
        search: List only collections whose names contain this term.
            When ``None`` or empty, all are returned.

    Returns:
        The matching collections, as :class:`CollectionResponseSchema`
        (empty if none match).
    """
    query = (ListObjectCollectionsGetParameters, {"search": search or None})

    return self._request("GET", "/list/object/collections", query=query, response_type=list[CollectionResponseSchema])

  # ---------------------------------------------------------------------------
  @route("GET", "/list/object/org-collections")
  def list(self: OrgCollections,
           organization_id: OrganizationId,
           search: Optional[str] = None) -> Union[list[CollectionResponseSchema], Any]:
    """List Collections from a specified Organization.

    Collections you do not have access to will not be listed.

    By default, this will return a list of all Collections, however you
    can specify search terms as additional query parameters to narrow list
    results.

    Args:
        organization_id: Unique identifier of the organization.
        search: Only collections whose names contain it; empty for all.

    Returns:
        The matching collections, as :class:`CollectionResponseSchema`,
        without their groups and users (empty if none match).
    """
    return self._request(
      "GET",
      "/list/object/org-collections",
      query=(ListObjectOrgCollectionsGetParameters, {
        "organizationId": organization_id,
        "search": search or None
      }),
      response_type=list[CollectionResponseSchema],
    )
