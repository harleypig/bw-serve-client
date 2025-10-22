"""Bitwarden Vault Management API Models.

Generated from OpenAPI specification.
DO NOT EDIT MANUALLY.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal, Sequence
from uuid import UUID

from pydantic import AnyUrl
from pydantic import AwareDatetime
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import EmailStr
from pydantic import Field
from pydantic import RootModel


class Type(Enum):
  """Type of vault item (1=login, 2=note, 3=card, 4=identity)."""
  INTEGER_1 = 1
  INTEGER_2 = 2
  INTEGER_3 = 3
  INTEGER_4 = 4


class Reprompt(Enum):
  """Master password re-prompt requirement (0=none, 1=required)."""
  INTEGER_0 = 0
  INTEGER_1 = 1


class ItemSecureNoteSchema(BaseModel):
  """Secure note data schema for vault items."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  type: Literal[0] | None
  """Secure note type (always 0)."""


class ItemCardSchema(BaseModel):
  """Credit card data schema for vault items."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  cardholder_name: Annotated[str | None, Field(alias='cardholderName')]
  brand: Literal['visa'] | None
  number: str | None
  exp_month: Annotated[str | None, Field(alias='expMonth')]
  exp_year: Annotated[str | None, Field(alias='expYear')]
  code: str | None


class ItemIdentitySchema(BaseModel):
  """Identity data schema for vault items."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  title: str | None
  first_name: Annotated[str | None, Field(alias='firstName')]
  middle_name: Annotated[str | None, Field(alias='middleName')]
  last_name: Annotated[str | None, Field(alias='lastName')]
  address1: str | None
  address2: str | None
  address3: str | None
  city: str | None
  state: str | None
  postal_code: Annotated[str | None, Field(alias='postalCode')]
  country: str | None
  company: str | None
  email: str | None
  phone: str | None
  ssn: str | None
  username: str | None
  passport_number: Annotated[str | None, Field(alias='passportNumber')]
  license_number: Annotated[str | None, Field(alias='licenseNumber')]


class Match(Enum):
  """URI matching behavior (0=domain, 1=host, 2=startsWith, 3=exact, 4=regex, 5=never)."""
  INTEGER_0 = 0
  INTEGER_1 = 1
  INTEGER_2 = 2
  INTEGER_3 = 3
  INTEGER_4 = 4
  INTEGER_5 = 5


class UrisSchema(BaseModel):
  """URI collection schema for login items."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  match: Match | None
  """URI matching behavior (0=domain, 1=host, 2=startsWith, 3=exact, 4=regex, 5=never)."""
  uri: str | None
  """The URI/URL value."""


class FieldTypeEnum(Enum):
  """Field type (0=text, 1=hidden, 2=boolean, 3=linked)."""
  FIELD_0 = 0
  FIELD_1 = 1
  FIELD_2 = 2
  FIELD_3 = 3


class FieldSchema(BaseModel):
  """Custom field schema for vault items."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  name: str | None
  """Name of the custom field."""
  value: str | None
  """Value of the custom field."""
  type: Annotated[FieldTypeEnum | None, Field(title='FieldTypeEnum')]
  """Field type (0=text, 1=hidden, 2=boolean, 3=linked)."""


class FolderSchema(BaseModel):
  """Folder schema for organizing vault items."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  name: str | None
  """Name of the folder."""


class SendTypeEnum(Enum):
  """Type of Send (0=text, 1=file)."""
  INTEGER_0 = 0
  INTEGER_1 = 1


class SendTextSchema(BaseModel):
  """Text content schema for Bitwarden Send items."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  text: str | None
  """Text content of the Send."""
  hidden: bool | None
  """Whether the text is hidden by default."""


class GroupSchema(BaseModel):
  """Group schema for user management."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  id: UUID | None
  read_only: Annotated[bool | None, Field(alias='readOnly')]
  hide_passwords: Annotated[bool | None, Field(alias='hidePasswords')]


class StatusEnum(Enum):
  """Vault status (locked, unlocked, or unauthenticated)."""
  LOCKED = 'locked'
  UNLOCKED = 'unlocked'
  UNAUTHENTICATED = 'unauthenticated'


class TemplateSchema(BaseModel):
  """Vault template schema containing server URL, sync info, and user details."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  server_url: Annotated[AnyUrl | None, Field(alias='serverUrl')]
  last_sync: Annotated[AwareDatetime | None, Field(alias='lastSync')]
  user_email: Annotated[EmailStr | None, Field(alias='userEmail')]
  user_id: Annotated[UUID | None, Field(alias='userID')]
  status: Annotated[StatusEnum | None, Field(title='StatusEnum')]
  """Vault status (locked, unlocked, or unauthenticated)."""


class StatusDataSchema(BaseModel):
  """Status response data containing template information."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  object: Literal['template'] | None
  template: Annotated[TemplateSchema | None, Field(title='TemplateSchema')]
  """Vault template schema containing server URL, sync info, and user details."""


class StatusSchema(BaseModel):
  """Status of the vault (locked, unlocked, or unauthenticated)."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  success: bool | None
  data: Annotated[StatusDataSchema | None, Field(title='StatusDataSchema')]
  """Status response data containing template information."""


class LockUnlockDataSchema(BaseModel):
  """Data schema for lock/unlock response containing status message and display options."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  no_color: Annotated[bool | None, Field(alias='noColor')]
  object: str | None
  title: str | None
  message: str | None


class LockUnlockSuccessSchema(BaseModel):
  """Success response schema for lock/unlock operations."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  success: bool | None
  data: Annotated[LockUnlockDataSchema | None, Field(title='LockUnlockDataSchema')]
  """Data schema for lock/unlock response containing status message and display options."""


class DeviceApprovalPropertiesSchema(BaseModel):
  """Device approval properties schema for organization management."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  id: str | None
  user_id: Annotated[str | None, Field(alias='userId')]
  email: str | None
  request_device_identifier: Annotated[str | None, Field(alias='requestDeviceIdentifier')]
  request_device_type: Annotated[str | None, Field(alias='requestDeviceType')]
  request_ip_address: Annotated[str | None, Field(alias='requestIpAddress')]
  creation_date: Annotated[str | None, Field(alias='creationDate')]


class UnlockPostRequestSchema(BaseModel):
  """Request schema for unlocking the vault with master password."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  password: str | None


class ObjectItemIdPutParameters(BaseModel):
  id: Annotated[UUID, Field(title='ObjectItemIdPutParameters')]
  """Path parameters for editing an item in the vault."""


class ObjectItemIdGetParameters(BaseModel):
  id: Annotated[UUID, Field(title='ObjectItemIdGetParameters')]
  """Path parameters for retrieving an item from the vault."""


class ObjectItemIdDeleteParameters(BaseModel):
  id: Annotated[UUID, Field(title='ObjectItemIdDeleteResponse')]
  """Path parameters for deleting an item from the vault."""


class ObjectItemIdDeleteResponse(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  success: bool | None


class RestoreItemIdPostParameters(BaseModel):
  id: UUID


RestoreItemIdPostResponse = ObjectItemIdDeleteResponse


class ListObjectItemsGetParameters(BaseModel):
  organization_id: Annotated[
    UUID | None,
    Field(alias='organizationId', title='ListObjectItemsGetParameters')]
  """Query parameters for listing items in the vault."""
  collection_id: Annotated[UUID | None, Field(alias='collectionId')]
  folderid: UUID | None
  url: AnyUrl | None
  trash: bool | None
  search: str | None


class AttachmentPostParameters(BaseModel):
  itemid: Annotated[UUID, Field(title='AttachmentPostParameters')]
  """Query parameters for attaching a file to an item."""


class AttachmentPostRequest(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  file: bytes | None


class ObjectAttachmentIdGetParameters(BaseModel):
  id: Annotated[UUID, Field(title='ObjectAttachmentIdGetParameters')]
  """Path parameters for retrieving an attachment."""
  itemid: UUID


class ObjectAttachmentIdDeleteParameters(BaseModel):
  id: UUID
  itemid: UUID


ObjectUsernameIdGetParameters = RestoreItemIdPostParameters

ObjectPasswordIdGetParameters = RestoreItemIdPostParameters

ObjectUriIdGetParameters = RestoreItemIdPostParameters

ObjectTotpIdGetParameters = RestoreItemIdPostParameters

ObjectNotesIdGetParameters = RestoreItemIdPostParameters

ObjectExposedIdGetParameters = RestoreItemIdPostParameters


class ObjectFolderPostResponse(BaseModel):
  """Response schema for creating a folder."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  success: bool | None
  data: FolderSchema | None


ObjectFolderIdPutParameters = RestoreItemIdPostParameters


class ObjectFolderIdPutResponse(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  success: bool | None
  data: FolderSchema | None


ObjectFolderIdGetParameters = RestoreItemIdPostParameters

ObjectFolderIdGetResponse = ObjectFolderIdPutResponse

ObjectFolderIdDeleteParameters = RestoreItemIdPostParameters

ObjectFolderIdDeleteResponse = ObjectItemIdDeleteResponse


class ListObjectFoldersGetParameters(BaseModel):
  search: Annotated[str | None, Field(title='ListObjectFoldersGetParameters')]
  """Query parameters for listing folders."""


class FolderListDataSchema(BaseModel):
  """List data schema containing array of folder objects."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  object: Literal['list'] | None
  data: Sequence[FolderSchema] | None


class ListObjectFoldersGetResponse(BaseModel):
  """Response schema for listing folders."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  success: bool | None
  data: Annotated[FolderListDataSchema | None, Field(title='FolderListDataSchema')]
  """List data schema containing array of folder objects."""


class ObjectSendIdPutParameters(BaseModel):
  id: Annotated[UUID, Field(title='ObjectSendIdPutResponse')]
  """Path parameters for updating a send."""


ObjectSendIdGetParameters = RestoreItemIdPostParameters

ObjectSendIdDeleteParameters = RestoreItemIdPostParameters

ObjectSendIdDeleteResponse = ObjectItemIdDeleteResponse


class ListObjectSendGetParameters(BaseModel):
  search: Annotated[str | None, Field(title='ListObjectSendGetResponse')]
  """Response schema for listing sends."""


SendIdRemovePasswordPostParameters = RestoreItemIdPostParameters


class MoveItemidOrganizationIdPostParameters(BaseModel):
  itemid: Annotated[UUID, Field(title='MoveItemidOrganizationIdPostParameters')]
  """Path parameters for moving an item to a collection."""
  organization_id: Annotated[
    UUID, Field(alias='organizationId', title='MoveItemidOrganizationIdPostRequest')]
  """Request schema for moving an item to a collection."""


class MoveItemidOrganizationIdPostRequest(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  array: Sequence[str] | None


class ObjectOrgCollectionPostParameters(BaseModel):
  organization_id: Annotated[
    UUID, Field(alias='organizationId', title='ObjectOrgCollectionPostParameters')]
  """Path parameters for creating an organization collection."""


class ObjectOrgCollectionIdPutParameters(BaseModel):
  id: Annotated[UUID, Field(title='ObjectOrgCollectionIdPutParameters')]
  """Path parameters for updating an organization collection."""
  organization_id: Annotated[UUID, Field(alias='organizationId')]


class ObjectOrgCollectionIdGetParameters(BaseModel):
  id: UUID
  organization_id: Annotated[UUID, Field(alias='organizationId')]


ObjectOrgCollectionIdDeleteParameters = ObjectOrgCollectionIdGetParameters


class ListObjectOrgCollectionsGetParameters(BaseModel):
  organization_id: Annotated[
    UUID,
    Field(alias='organizationId', title='ListObjectOrgCollectionsGetParameters')]
  """Query parameters for listing organization collections."""
  search: str | None


class ListObjectCollectionsGetParameters(BaseModel):
  search: Annotated[str | None, Field(title='ListObjectCollectionsGetParameters')]
  """Query parameters for listing collections."""


class ListObjectOrganizationsGetParameters(BaseModel):
  search: str | None


class ListObjectOrgMembersGetParameters(BaseModel):
  organization_id: Annotated[
    UUID, Field(alias='organizationId', title='ListObjectOrgMembersGetParameters')]
  """Query parameters for listing organization members."""


ConfirmOrgMemberIdPostParameters = ObjectOrgCollectionIdGetParameters


class DeviceApprovalOrganizationIdGetParameters(BaseModel):
  organization_id: Annotated[UUID, Field(alias='organizationId')]


DeviceApprovalOrganizationIdApproveAllPostParameters = DeviceApprovalOrganizationIdGetParameters


class DeviceApprovalOrganizationIdDenyRequestIdPostParameters(BaseModel):
  organization_id: Annotated[UUID, Field(alias='organizationId')]
  request_id: Annotated[
    UUID,
    Field(
      alias='request-id', title='DeviceApprovalOrganizationIdDenyRequestIdPostParameters'
    )]
  """Path parameters for denying a device approval request."""


DeviceApprovalOrganizationIdDenyAllPostParameters = DeviceApprovalOrganizationIdGetParameters


class GenerateGetParameters(BaseModel):
  length: Annotated[int | None, Field(title='GenerateGetParameters')]
  """Query parameters for generating passwords."""
  uppercase: bool | None
  lowercase: bool | None
  number: bool | None
  special: bool | None
  passphrase: bool | None
  words: int | None
  separator: str | None
  capitalize: bool | None
  include_number: Annotated[bool | None, Field(alias='includeNumber')]


class ObjectTemplateTypeGetParameters1(Enum):
  """Path parameters for retrieving template by type."""
  ITEM = 'item'
  ITEM_FIELD = 'item.field'
  ITEM_LOGIN = 'item.login'
  ITEM_LOGIN_URI = 'item.login.uri'
  ITEM_CARD = 'item.card'
  ITEM_IDENTITY = 'item.identity'
  ITEM_SECURENOTE = 'item.securenote'
  FOLDER = 'folder'
  COLLECTION = 'collection'
  ITEM_COLLECTIONS = 'item-collections'
  ORG_COLLECTION = 'org-collection'


class ObjectTemplateTypeGetParameters(BaseModel):
  type: Annotated[ObjectTemplateTypeGetParameters1,
                  Field(title='ObjectTemplateTypeGetParameters')]
  """Path parameters for retrieving template by type."""


class DeviceApprovalOrganizationIdApproveRequestIdPostParameters(BaseModel):
  organization_id: Annotated[
    UUID,
    Field(
      alias='organizationId',
      title='DeviceApprovalOrganizationIdApproveRequestIdPostParameters'
    )]
  """Path parameters for approving a device approval request."""
  request_id: Annotated[UUID, Field(alias='request-id')]


class ItemLoginSchema(BaseModel):
  """Login-specific data schema for vault items."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  uris: UrisSchema | None
  """Array of URIs associated with this login."""
  username: str | None
  """Username for the login."""
  password: str | None
  """Password for the login."""
  totp: str | None
  """TOTP secret for two-factor authentication."""


class SendTemplateSchema(BaseModel):
  """Template schema for Bitwarden Send items."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  name: str | None
  """Name of the Send."""
  notes: str | None
  """Notes for the Send."""
  type: Annotated[SendTypeEnum | None, Field(title='SendTypeEnum')]
  """Type of Send (0=text, 1=file)."""
  text: SendTextSchema | None
  file: str | None
  max_access_count: Annotated[int | None, Field(alias='maxAccessCount')]
  deletion_date: Annotated[AwareDatetime | None, Field(alias='deletionDate')]
  expiration_date: Annotated[AwareDatetime | None, Field(alias='expirationDate')]
  password: str | None
  disabled: bool | None
  hide_email: Annotated[bool | None, Field(alias='hideEmail')]


class CollectionSchema(BaseModel):
  """Collection schema for organizing vault items."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  organization_id: Annotated[UUID | None, Field(alias='organizationId')]
  name: str | None
  external_id: Annotated[str | None, Field(alias='externalId')]
  groups: Sequence[GroupSchema] | None


class DeviceApprovalListSchema(RootModel[Sequence[DeviceApprovalPropertiesSchema]]):
  """Device approval list schema for organization management."""
  model_config = ConfigDict(populate_by_name=True,)
  root: Annotated[Sequence[DeviceApprovalPropertiesSchema],
                  Field(title='DeviceApprovalListSchema')]
  """Device approval list schema for organization management."""


class ObjectSendPostResponse(BaseModel):
  """Response schema for creating a send."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  success: bool | None
  data: SendTemplateSchema | None


class ObjectSendIdPutResponse(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  success: bool | None
  data: SendTemplateSchema | None


ObjectSendIdGetResponse = ObjectSendIdPutResponse


class SendListDataSchema(BaseModel):
  """List data schema containing array of send templates."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  object: Literal['list'] | None
  data: Sequence[SendTemplateSchema] | None


class ListObjectSendGetResponse(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  success: bool | None
  data: Annotated[SendListDataSchema | None, Field(title='SendListDataSchema')]
  """List data schema containing array of send templates."""


SendIdRemovePasswordPostResponse = ObjectSendIdPutResponse


class ItemTemplateSchema(BaseModel):
  """Template schema for vault items with all possible fields."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  organization_id: Annotated[UUID | None, Field(alias='organizationId')]
  """Organization ID if item belongs to an organization."""
  collection_ids: Annotated[Sequence[UUID] | None, Field(alias='collectionIds')]
  """Array of collection IDs for organization items."""
  folder_id: Annotated[UUID | None, Field(alias='folderId')]
  """Folder ID for organizing the item."""
  type: Type | None
  """Type of vault item (1=login, 2=note, 3=card, 4=identity)."""
  name: str | None
  """Display name of the vault item."""
  notes: str | None
  """Free-form notes associated with the item."""
  favorite: bool | None
  """Whether the item is marked as a favorite."""
  fields: Sequence[FieldSchema] | None
  """Array of custom fields."""
  login: ItemLoginSchema | None
  """Login-specific data (username, password, URIs, TOTP)."""
  secure_note: Annotated[ItemSecureNoteSchema | None, Field(alias='secureNote')]
  """Secure note data."""
  card: ItemCardSchema | None
  """Credit card data."""
  identity: ItemIdentitySchema | None
  """Identity data."""
  reprompt: Reprompt | None
  """Master password re-prompt requirement (0=none, 1=required)."""


class ObjectItemPostResponse(BaseModel):
  """Response schema for creating an item."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  success: bool | None
  data: ItemTemplateSchema | None
  revision_date: Annotated[AwareDatetime | None, Field(alias='revisionDate')]
  delete_date: Annotated[AwareDatetime | None, Field(alias='deleteDate')] = None


class ObjectItemIdPutResponse(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  success: bool | None
  data: ItemTemplateSchema | None
  revision_date: Annotated[AwareDatetime | None, Field(alias='revisionDate')]
  delete_date: Annotated[AwareDatetime | None, Field(alias='deleteDate')] = None


ObjectItemIdGetResponse = ObjectItemIdPutResponse


class ItemListDataSchema(BaseModel):
  """List data schema containing array of item templates."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  object: Literal['list'] | None
  data: Sequence[ItemTemplateSchema] | None


class ListObjectItemsGetResponse(BaseModel):
  """Response schema for listing items."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  success: bool | None
  data: Annotated[ItemListDataSchema | None, Field(title='ItemListDataSchema')]
  """List data schema containing array of item templates."""
