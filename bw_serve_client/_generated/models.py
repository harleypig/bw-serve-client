"""Bitwarden Vault Management API Models.

Generated from OpenAPI specification.
DO NOT EDIT MANUALLY.
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import Enum
from enum import IntEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AnyUrl
from pydantic import AwareDatetime
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import EmailStr
from pydantic import Field
from pydantic import RootModel
from pydantic import SecretStr


class ItemTypeSchema(IntEnum):
  """Type of vault item (1=login, 2=note, 3=card, 4=identity)."""
  INTEGER_1 = 1
  INTEGER_2 = 2
  INTEGER_3 = 3
  INTEGER_4 = 4


class RepromptSchema(IntEnum):
  """Master password re-prompt requirement (0=none, 1=required)."""
  INTEGER_0 = 0
  INTEGER_1 = 1


class ItemSecureNoteSchema(BaseModel):
  """Secure note data schema for vault items."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  type: Annotated[Literal[0] | None, Field(description='Secure note type (always 0)', title='SecureNoteTypeSchema')]


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


class MatchSchema(IntEnum):
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
  match: Annotated[
    MatchSchema | None,
    Field(description='URI matching behavior (0=domain, 1=host, 2=startsWith, 3=exact, 4=regex, 5=never)', title='MatchSchema')]
  uri: Annotated[str | None, Field(description='The URI/URL value')]


class FieldTypeSchema(Enum):
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
  name: Annotated[str | None, Field(description='Name of the custom field', title='FieldNameSchema')]
  value: Annotated[str | None, Field(description='Value of the custom field', title='FieldValueSchema')]
  type: Annotated[FieldTypeSchema | None,
                  Field(description='Field type (0=text, 1=hidden, 2=boolean, 3=linked)', title='FieldTypeSchema')]


class FolderSchema(BaseModel):
  """Folder schema for organizing vault items."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  name: Annotated[str | None, Field(description='Name of the folder')]


class SendTypeSchema(IntEnum):
  """Type of Send (0=text, 1=file)."""
  INTEGER_0 = 0
  INTEGER_1 = 1


class SendTextSchema(BaseModel):
  """Text content schema for Bitwarden Send items."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  text: Annotated[str | None, Field(description='Text content of the Send')]
  hidden: Annotated[bool | None, Field(description='Whether the text is hidden by default')]


class GroupSchema(BaseModel):
  """Group schema for user management."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  id: UUID | None
  read_only: Annotated[bool | None, Field(alias='readOnly')]
  hide_passwords: Annotated[bool | None, Field(alias='hidePasswords')]


class TemplateStatusSchema(Enum):
  """Vault status (locked, unlocked, or unauthenticated)."""
  LOCKED = 'locked'
  UNLOCKED = 'unlocked'
  UNAUTHENTICATED = 'unauthenticated'


class TemplateSchema(BaseModel):
  """Vault template schema containing server URL, sync info, and user details."""
  model_config = ConfigDict(
    extra='ignore',
    populate_by_name=True,
  )
  server_url: Annotated[AnyUrl | None, Field(alias='serverUrl')]
  last_sync: Annotated[AwareDatetime | None, Field(alias='lastSync')]
  user_email: Annotated[EmailStr | None, Field(alias='userEmail')]
  user_id: Annotated[UUID | None, Field(alias='userId')]
  status: Annotated[TemplateStatusSchema | None,
                    Field(description='Vault status (locked, unlocked, or unauthenticated)', title='TemplateStatusSchema')]


class StatusDataSchema(BaseModel):
  """Status response data containing template information."""
  model_config = ConfigDict(
    extra='ignore',
    populate_by_name=True,
  )
  object: Literal['template'] | None
  template: Annotated[
    TemplateSchema | None,
    Field(description='Vault template schema containing server URL, sync info, and user details', title='TemplateSchema')]


class StatusSchema(BaseModel):
  """AGENT: fixme."""
  model_config = ConfigDict(
    extra='ignore',
    populate_by_name=True,
  )
  success: bool | None
  data: Annotated[StatusDataSchema | None,
                  Field(description='Status response data containing template information', title='StatusDataSchema')]


class LockUnlockDataSchema(BaseModel):
  """Data schema for lock/unlock response containing status message and display options."""
  model_config = ConfigDict(
    extra='ignore',
    populate_by_name=True,
  )
  no_color: Annotated[bool | None, Field(alias='noColor')]
  object: str | None
  title: str | None
  message: SecretStr | None
  raw: SecretStr | None


class LockUnlockSuccessSchema(BaseModel):
  """Success response schema for lock/unlock operations."""
  model_config = ConfigDict(
    extra='ignore',
    populate_by_name=True,
  )
  success: bool | None
  data: Annotated[LockUnlockDataSchema | None,
                  Field(
                    description='Data schema for lock/unlock response containing status message and display options',
                    title='LockUnlockDataSchema'
                  )]


class DeviceApprovalPropertiesSchema(BaseModel):
  """Device approval properties schema for organization management."""
  model_config = ConfigDict(
    extra='ignore',
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
  password: SecretStr | None


class IdSchema(RootModel[UUID]):
  root: Annotated[UUID, Field(title='IdSchema')]


class ObjectItemIdPutParameters(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  id: Annotated[UUID, Field(title='IdSchema')]


class ObjectItemIdGetParameters(ObjectItemIdPutParameters):
  pass


class ObjectItemIdDeleteParameters(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  id: Annotated[UUID, Field(title='IdSchema')]
  permanent: Annotated[bool | None, Field(title='PermanentSchema')]


class ObjectItemCollectionsIdGetParameters(ObjectItemIdPutParameters):
  pass


class ObjectItemCollectionsIdPutParameters(ObjectItemIdPutParameters):
  pass


class ObjectItemCollectionsIdPutRequest(RootModel[Sequence[UUID]]):
  root: Sequence[UUID]


class RestoreItemIdPostParameters(ObjectItemIdPutParameters):
  pass


class ArchiveObjectIdPostParameters(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  object: Annotated[Literal['item'], Field(title='ObjectSchema')]
  id: Annotated[UUID, Field(title='IdSchema')]


class OrganizationIdSchema1(RootModel[UUID]):
  root: Annotated[UUID, Field(title='OrganizationIdSchema')]


class SearchSchema(RootModel[str]):
  root: Annotated[str, Field(title='SearchSchema')]


class ListObjectItemsGetParameters(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  organization_id: Annotated[UUID | None, Field(alias='organizationId', title='OrganizationIdSchema')]
  collection_id: Annotated[UUID | None, Field(alias='collectionId', title='CollectionIdSchema')]
  folderid: Annotated[UUID | None, Field(title='FolderIdSchema')]
  url: Annotated[AnyUrl | None, Field(title='UrlSchema')]
  trash: Annotated[bool | None, Field(title='TrashSchema')]
  archived: Annotated[bool | None, Field(title='ArchivedSchema')]
  search: Annotated[str | None, Field(title='SearchSchema')]


class ItemIdSchema(RootModel[UUID]):
  root: Annotated[UUID, Field(title='ItemIdSchema')]


class AttachmentPostParameters(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  itemid: Annotated[UUID, Field(title='ItemIdSchema')]


class AttachmentRequestSchema(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  file: bytes | None


class ObjectAttachmentIdGetParameters(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  id: Annotated[UUID, Field(title='IdSchema')]
  itemid: Annotated[UUID, Field(title='ItemIdSchema')]


class ObjectAttachmentIdDeleteParameters(ObjectAttachmentIdGetParameters):
  pass


class ObjectUsernameIdGetParameters(ObjectItemIdPutParameters):
  pass


class ObjectPasswordIdGetParameters(ObjectItemIdPutParameters):
  pass


class ObjectUriIdGetParameters(ObjectItemIdPutParameters):
  pass


class ObjectTotpIdGetParameters(ObjectItemIdPutParameters):
  pass


class ObjectNotesIdGetParameters(ObjectItemIdPutParameters):
  pass


class ObjectExposedIdGetParameters(ObjectItemIdPutParameters):
  pass


class ObjectFolderIdPutParameters(ObjectItemIdPutParameters):
  pass


class ObjectFolderIdGetParameters(ObjectItemIdPutParameters):
  pass


class ObjectFolderIdDeleteParameters(ObjectItemIdPutParameters):
  pass


class ListObjectFoldersGetParameters(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  search: Annotated[str | None, Field(title='SearchSchema')]


class ObjectSendIdPutParameters(ObjectItemIdPutParameters):
  pass


class ObjectSendIdGetParameters(ObjectItemIdPutParameters):
  pass


class ObjectSendIdDeleteParameters(ObjectItemIdPutParameters):
  pass


class ListObjectSendGetParameters(ListObjectFoldersGetParameters):
  pass


class SendListGetParameters(ListObjectFoldersGetParameters):
  pass


class SendIdRemovePasswordPostParameters(ObjectItemIdPutParameters):
  pass


class MoveItemidOrganizationIdPostParameters(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  itemid: Annotated[UUID, Field(title='ItemIdSchema')]
  organization_id: Annotated[UUID, Field(alias='organizationId', title='OrganizationIdSchema')]


class MoveItemRequestSchema(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  array: Sequence[str] | None


class ObjectOrgCollectionPostParameters(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  organization_id: Annotated[UUID, Field(alias='organizationId', title='OrganizationIdSchema')]


class ObjectOrgCollectionIdPutParameters(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  id: Annotated[UUID, Field(title='IdSchema')]
  organization_id: Annotated[UUID, Field(alias='organizationId', title='OrganizationIdSchema')]


class ObjectOrgCollectionIdGetParameters(ObjectOrgCollectionIdPutParameters):
  pass


class ObjectOrgCollectionIdDeleteParameters(ObjectOrgCollectionIdPutParameters):
  pass


class ListObjectOrgCollectionsGetParameters(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  organization_id: Annotated[UUID, Field(alias='organizationId', title='OrganizationIdSchema')]
  search: Annotated[str | None, Field(title='SearchSchema')]


class ListObjectCollectionsGetParameters(ListObjectFoldersGetParameters):
  pass


class ListObjectOrganizationsGetParameters(ListObjectFoldersGetParameters):
  pass


class ListObjectOrgMembersGetParameters(ObjectOrgCollectionPostParameters):
  pass


class ObjectCollectionIdGetParameters(ObjectItemIdPutParameters):
  pass


class ObjectOrganizationIdGetParameters(ObjectItemIdPutParameters):
  pass


class ConfirmOrgMemberIdPostParameters(ObjectOrgCollectionIdPutParameters):
  pass


class DeviceApprovalOrganizationIdGetParameters(ObjectOrgCollectionPostParameters):
  pass


class RequestIdSchema(RootModel[UUID]):
  root: Annotated[UUID, Field(title='RequestIdSchema')]


class DeviceApprovalOrganizationIdApproveRequestIdPostParameters(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  organization_id: Annotated[UUID, Field(alias='organizationId', title='OrganizationIdSchema')]
  request_id: Annotated[UUID, Field(alias='request-id', title='RequestIdSchema')]


class DeviceApprovalOrganizationIdApproveAllPostParameters(ObjectOrgCollectionPostParameters):
  pass


class DeviceApprovalOrganizationIdDenyRequestIdPostParameters(DeviceApprovalOrganizationIdApproveRequestIdPostParameters):
  pass


class DeviceApprovalOrganizationIdDenyAllPostParameters(ObjectOrgCollectionPostParameters):
  pass


class SyncPostParameters(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  force: Annotated[bool | None, Field(title='ForceSchema')]


class GenerateGetParameters(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  length: Annotated[int | None, Field(title='LengthSchema')]
  uppercase: Annotated[bool | None, Field(title='UppercaseSchema')]
  lowercase: Annotated[bool | None, Field(title='LowercaseSchema')]
  number: Annotated[bool | None, Field(title='NumberSchema')]
  special: Annotated[bool | None, Field(title='SpecialSchema')]
  passphrase: Annotated[bool | None, Field(title='PassphraseSchema')]
  words: Annotated[int | None, Field(title='WordsSchema')]
  separator: Annotated[str | None, Field(title='SeparatorSchema')]
  capitalize: Annotated[bool | None, Field(title='CapitalizeSchema')]
  include_number: Annotated[bool | None, Field(alias='includeNumber', title='NumberSchema')]
  min_number: Annotated[int | None, Field(alias='minNumber', title='MinNumberSchema')]
  min_special: Annotated[int | None, Field(alias='minSpecial', title='MinSpecialSchema')]
  ambiguous: Annotated[bool | None, Field(title='AmbiguousSchema')]


class TypeSchema(Enum):
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
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  type: Annotated[TypeSchema, Field(title='TypeSchema')]


class ItemLoginSchema(BaseModel):
  """Login-specific data schema for vault items."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  uris: Annotated[UrisSchema | None, Field(description='Array of URIs associated with this login')]
  username: Annotated[str | None, Field(description='Username for the login')]
  password: Annotated[str | None, Field(description='Password for the login')]
  totp: Annotated[str | None, Field(description='TOTP secret for two-factor authentication')]


class SendTemplateSchema(BaseModel):
  """Template schema for Bitwarden Send items."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  name: Annotated[str | None, Field(description='Name of the Send', title='SendNameSchema')]
  notes: Annotated[str | None, Field(description='Notes for the Send', title='SendNotesSchema')]
  type: Annotated[SendTypeSchema | None, Field(description='Type of Send (0=text, 1=file)', title='SendTypeSchema')]
  text: SendTextSchema | None
  file: Annotated[str | None, Field(title='SendFileSchema')]
  max_access_count: Annotated[int | None, Field(alias='maxAccessCount', title='SendMaxAccessCountSchema')]
  deletion_date: Annotated[AwareDatetime | None, Field(alias='deletionDate', title='SendDeletionDateSchema')]
  expiration_date: Annotated[AwareDatetime | None, Field(alias='expirationDate', title='SendExpirationDateSchema')]
  password: Annotated[str | None, Field(title='SendPasswordSchema')]
  emails: Sequence[EmailStr] | None
  disabled: Annotated[bool | None, Field(title='SendDisabledSchema')]
  hide_email: Annotated[bool | None, Field(alias='hideEmail', title='SendHideEmailSchema')]


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
  root: Annotated[Sequence[DeviceApprovalPropertiesSchema],
                  Field(description='Device approval list schema for organization management', title='DeviceApprovalListSchema')]


class ItemTemplateSchema(BaseModel):
  """Template schema for vault items with all possible fields."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  organization_id: Annotated[
    UUID | None,
    Field(alias='organizationId', description='Organization ID if item belongs to an organization', title='OrganizationIdSchema')]
  collection_ids: Annotated[
    Sequence[UUID] | None,
    Field(alias='collectionIds', description='Array of collection IDs for organization items', title='CollectionIdsSchema')]
  folder_id: Annotated[UUID | None,
                       Field(alias='folderId', description='Folder ID for organizing the item', title='FolderIdSchema')]
  type: Annotated[ItemTypeSchema | None,
                  Field(description='Type of vault item (1=login, 2=note, 3=card, 4=identity)', title='ItemTypeSchema')]
  name: Annotated[str | None, Field(description='Display name of the vault item', title='ItemNameSchema')]
  notes: Annotated[str | None, Field(description='Free-form notes associated with the item', title='ItemNotesSchema')]
  favorite: Annotated[bool | None, Field(description='Whether the item is marked as a favorite', title='ItemFavoriteSchema')]
  fields: Annotated[Sequence[FieldSchema] | None, Field(description='Array of custom fields', title='ItemFieldsSchema')]
  login: Annotated[ItemLoginSchema | None, Field(description='Login-specific data (username, password, URIs, TOTP)')]
  secure_note: Annotated[ItemSecureNoteSchema | None, Field(alias='secureNote', description='Secure note data')]
  card: Annotated[ItemCardSchema | None, Field(description='Credit card data')]
  identity: Annotated[ItemIdentitySchema | None, Field(description='Identity data')]
  reprompt: Annotated[RepromptSchema | None,
                      Field(description='Master password re-prompt requirement (0=none, 1=required)', title='RepromptSchema')]


__all__ = [
  "ItemTypeSchema", "RepromptSchema", "ItemSecureNoteSchema", "ItemCardSchema", "ItemIdentitySchema", "MatchSchema", "UrisSchema",
  "FieldTypeSchema", "FieldSchema", "FolderSchema", "SendTypeSchema", "SendTextSchema", "GroupSchema", "TemplateStatusSchema",
  "TemplateSchema", "StatusDataSchema", "StatusSchema", "LockUnlockDataSchema", "LockUnlockSuccessSchema",
  "DeviceApprovalPropertiesSchema", "UnlockPostRequestSchema", "IdSchema", "ObjectItemIdPutParameters", "ObjectItemIdGetParameters",
  "ObjectItemIdDeleteParameters", "ObjectItemCollectionsIdGetParameters", "ObjectItemCollectionsIdPutParameters",
  "ObjectItemCollectionsIdPutRequest", "RestoreItemIdPostParameters", "ArchiveObjectIdPostParameters", "OrganizationIdSchema1",
  "SearchSchema", "ListObjectItemsGetParameters", "ItemIdSchema", "AttachmentPostParameters", "AttachmentRequestSchema",
  "ObjectAttachmentIdGetParameters", "ObjectAttachmentIdDeleteParameters", "ObjectUsernameIdGetParameters",
  "ObjectPasswordIdGetParameters", "ObjectUriIdGetParameters", "ObjectTotpIdGetParameters", "ObjectNotesIdGetParameters",
  "ObjectExposedIdGetParameters", "ObjectFolderIdPutParameters", "ObjectFolderIdGetParameters", "ObjectFolderIdDeleteParameters",
  "ListObjectFoldersGetParameters", "ObjectSendIdPutParameters", "ObjectSendIdGetParameters", "ObjectSendIdDeleteParameters",
  "ListObjectSendGetParameters", "SendListGetParameters", "SendIdRemovePasswordPostParameters",
  "MoveItemidOrganizationIdPostParameters", "MoveItemRequestSchema", "ObjectOrgCollectionPostParameters",
  "ObjectOrgCollectionIdPutParameters", "ObjectOrgCollectionIdGetParameters", "ObjectOrgCollectionIdDeleteParameters",
  "ListObjectOrgCollectionsGetParameters", "ListObjectCollectionsGetParameters", "ListObjectOrganizationsGetParameters",
  "ListObjectOrgMembersGetParameters", "ObjectCollectionIdGetParameters", "ObjectOrganizationIdGetParameters",
  "ConfirmOrgMemberIdPostParameters", "DeviceApprovalOrganizationIdGetParameters", "RequestIdSchema",
  "DeviceApprovalOrganizationIdApproveRequestIdPostParameters", "DeviceApprovalOrganizationIdApproveAllPostParameters",
  "DeviceApprovalOrganizationIdDenyRequestIdPostParameters", "DeviceApprovalOrganizationIdDenyAllPostParameters",
  "SyncPostParameters", "GenerateGetParameters", "TypeSchema", "ObjectTemplateTypeGetParameters", "ItemLoginSchema",
  "SendTemplateSchema", "CollectionSchema", "DeviceApprovalListSchema", "ItemTemplateSchema"
]
