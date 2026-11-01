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
  type: Annotated[Literal[0] | None, Field(description='Secure note type (always 0)', title='SecureNoteTypeSchema')] = None


class ItemCardSchema(BaseModel):
  """Credit card data schema for vault items."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  cardholder_name: Annotated[str | None, Field(alias='cardholderName')] = None
  brand: Literal['visa'] | None = None
  number: str | None = None
  exp_month: Annotated[str | None, Field(alias='expMonth')] = None
  exp_year: Annotated[str | None, Field(alias='expYear')] = None
  code: str | None = None


class ItemIdentitySchema(BaseModel):
  """Identity data schema for vault items."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  title: str | None = None
  first_name: Annotated[str | None, Field(alias='firstName')] = None
  middle_name: Annotated[str | None, Field(alias='middleName')] = None
  last_name: Annotated[str | None, Field(alias='lastName')] = None
  address1: str | None = None
  address2: str | None = None
  address3: str | None = None
  city: str | None = None
  state: str | None = None
  postal_code: Annotated[str | None, Field(alias='postalCode')] = None
  country: str | None = None
  company: str | None = None
  email: str | None = None
  phone: str | None = None
  ssn: str | None = None
  username: str | None = None
  passport_number: Annotated[str | None, Field(alias='passportNumber')] = None
  license_number: Annotated[str | None, Field(alias='licenseNumber')] = None


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
    Field(description='URI matching behavior (0=domain, 1=host, 2=startsWith, 3=exact, 4=regex, 5=never)', title='MatchSchema')
  ] = None
  uri: Annotated[str | None, Field(description='The URI/URL value')] = None


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
  name: Annotated[str | None, Field(description='Name of the custom field', title='FieldNameSchema')] = None
  value: Annotated[str | None, Field(description='Value of the custom field', title='FieldValueSchema')] = None
  type: Annotated[FieldTypeSchema | None,
                  Field(description='Field type (0=text, 1=hidden, 2=boolean, 3=linked)', title='FieldTypeSchema')] = None


class FolderSchema(BaseModel):
  """Folder schema for organizing vault items."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  name: Annotated[str | None, Field(description='Name of the folder')] = None


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
  text: Annotated[str | None, Field(description='Text content of the Send')] = None
  hidden: Annotated[bool | None, Field(description='Whether the text is hidden by default')] = None


class GroupSchema(BaseModel):
  """Group schema for user management."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  id: UUID | None = None
  read_only: Annotated[bool | None, Field(alias='readOnly')] = None
  hide_passwords: Annotated[bool | None, Field(alias='hidePasswords')] = None


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
  server_url: Annotated[AnyUrl | None, Field(alias='serverUrl')] = None
  last_sync: Annotated[AwareDatetime | None, Field(alias='lastSync')] = None
  user_email: Annotated[EmailStr | None, Field(alias='userEmail')] = None
  user_id: Annotated[UUID | None, Field(alias='userId')] = None
  status: Annotated[TemplateStatusSchema | None,
                    Field(description='Vault status (locked, unlocked, or unauthenticated)', title='TemplateStatusSchema')] = None


class StatusDataSchema(BaseModel):
  """Status response data containing template information."""
  model_config = ConfigDict(
    extra='ignore',
    populate_by_name=True,
  )
  object: Literal['template'] | None = None
  template: Annotated[
    TemplateSchema | None,
    Field(description='Vault template schema containing server URL, sync info, and user details', title='TemplateSchema')] = None


class StatusSchema(BaseModel):
  """AGENT: fixme."""
  model_config = ConfigDict(
    extra='ignore',
    populate_by_name=True,
  )
  success: bool | None = None
  data: Annotated[StatusDataSchema | None,
                  Field(description='Status response data containing template information', title='StatusDataSchema')] = None


class LockUnlockDataSchema(BaseModel):
  """Data schema for lock/unlock response containing status message and display options."""
  model_config = ConfigDict(
    extra='ignore',
    populate_by_name=True,
  )
  no_color: Annotated[bool | None, Field(alias='noColor')] = None
  object: str | None = None
  title: str | None = None
  message: SecretStr | None = None
  raw: SecretStr | None = None


class LockUnlockSuccessSchema(BaseModel):
  """Success response schema for lock/unlock operations."""
  model_config = ConfigDict(
    extra='ignore',
    populate_by_name=True,
  )
  success: bool | None = None
  data: Annotated[LockUnlockDataSchema | None,
                  Field(
                    description='Data schema for lock/unlock response containing status message and display options',
                    title='LockUnlockDataSchema'
                  )] = None


class DeviceApprovalPropertiesSchema(BaseModel):
  """Device approval properties schema for organization management."""
  model_config = ConfigDict(
    extra='ignore',
    populate_by_name=True,
  )
  id: str | None = None
  user_id: Annotated[str | None, Field(alias='userId')] = None
  email: str | None = None
  request_device_identifier: Annotated[str | None, Field(alias='requestDeviceIdentifier')] = None
  request_device_type: Annotated[str | None, Field(alias='requestDeviceType')] = None
  request_ip_address: Annotated[str | None, Field(alias='requestIpAddress')] = None
  creation_date: Annotated[str | None, Field(alias='creationDate')] = None
  organization_user_id: Annotated[str | None, Field(alias='organizationUserId')] = None


class UnlockPostRequestSchema(BaseModel):
  """Request schema for unlocking the vault with master password."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  password: SecretStr | None = None


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
  permanent: Annotated[bool | None, Field(title='PermanentSchema')] = None


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
  organization_id: Annotated[UUID | None, Field(alias='organizationId', title='OrganizationIdSchema')] = None
  collection_id: Annotated[UUID | None, Field(alias='collectionId', title='CollectionIdSchema')] = None
  folderid: Annotated[UUID | None, Field(title='FolderIdSchema')] = None
  url: Annotated[AnyUrl | None, Field(title='UrlSchema')] = None
  trash: Annotated[bool | None, Field(title='TrashSchema')] = None
  archived: Annotated[bool | None, Field(title='ArchivedSchema')] = None
  search: Annotated[str | None, Field(title='SearchSchema')] = None


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
  file: bytes | None = None


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
  search: Annotated[str | None, Field(title='SearchSchema')] = None


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


class MoveItemRequestSchema(RootModel[Sequence[UUID]]):
  root: Annotated[Sequence[UUID], Field(title='MoveItemRequestSchema')]


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
  search: Annotated[str | None, Field(title='SearchSchema')] = None


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
  force: Annotated[bool | None, Field(title='ForceSchema')] = None


class GenerateGetParameters(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  length: Annotated[int | None, Field(title='LengthSchema')] = None
  uppercase: Annotated[bool | None, Field(title='UppercaseSchema')] = None
  lowercase: Annotated[bool | None, Field(title='LowercaseSchema')] = None
  number: Annotated[bool | None, Field(title='NumberSchema')] = None
  special: Annotated[bool | None, Field(title='SpecialSchema')] = None
  passphrase: Annotated[bool | None, Field(title='PassphraseSchema')] = None
  words: Annotated[int | None, Field(title='WordsSchema')] = None
  separator: Annotated[str | None, Field(title='SeparatorSchema')] = None
  capitalize: Annotated[bool | None, Field(title='CapitalizeSchema')] = None
  include_number: Annotated[bool | None, Field(alias='includeNumber', title='NumberSchema')] = None
  min_number: Annotated[int | None, Field(alias='minNumber', title='MinNumberSchema')] = None
  min_special: Annotated[int | None, Field(alias='minSpecial', title='MinSpecialSchema')] = None
  ambiguous: Annotated[bool | None, Field(title='AmbiguousSchema')] = None


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
  uris: Annotated[Sequence[UrisSchema] | None, Field(description='Array of URIs associated with this login')] = None
  username: Annotated[str | None, Field(description='Username for the login')] = None
  password: Annotated[str | None, Field(description='Password for the login')] = None
  totp: Annotated[str | None, Field(description='TOTP secret for two-factor authentication')] = None


class SendTemplateSchema(BaseModel):
  """Template schema for Bitwarden Send items."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  name: Annotated[str | None, Field(description='Name of the Send', title='SendNameSchema')] = None
  notes: Annotated[str | None, Field(description='Notes for the Send', title='SendNotesSchema')] = None
  type: Annotated[SendTypeSchema | None, Field(description='Type of Send (0=text, 1=file)', title='SendTypeSchema')] = None
  text: SendTextSchema | None = None
  file: Annotated[str | None, Field(title='SendFileSchema')] = None
  max_access_count: Annotated[int | None, Field(alias='maxAccessCount', title='SendMaxAccessCountSchema')] = None
  deletion_date: Annotated[AwareDatetime | None, Field(alias='deletionDate', title='SendDeletionDateSchema')] = None
  expiration_date: Annotated[AwareDatetime | None, Field(alias='expirationDate', title='SendExpirationDateSchema')] = None
  password: Annotated[str | None, Field(title='SendPasswordSchema')] = None
  emails: Sequence[EmailStr] | None = None
  disabled: Annotated[bool | None, Field(title='SendDisabledSchema')] = None
  hide_email: Annotated[bool | None, Field(alias='hideEmail', title='SendHideEmailSchema')] = None


class CollectionSchema(BaseModel):
  """Collection schema for organizing vault items."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  organization_id: Annotated[UUID | None, Field(alias='organizationId')] = None
  name: str | None = None
  external_id: Annotated[str | None, Field(alias='externalId')] = None
  groups: Sequence[GroupSchema] | None = None


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
    Field(alias='organizationId', description='Organization ID if item belongs to an organization', title='OrganizationIdSchema')
  ] = None
  collection_ids: Annotated[
    Sequence[UUID] | None,
    Field(alias='collectionIds', description='Array of collection IDs for organization items', title='CollectionIdsSchema')] = None
  folder_id: Annotated[UUID | None,
                       Field(alias='folderId', description='Folder ID for organizing the item', title='FolderIdSchema')] = None
  type: Annotated[ItemTypeSchema | None,
                  Field(description='Type of vault item (1=login, 2=note, 3=card, 4=identity)', title='ItemTypeSchema')] = None
  name: Annotated[str | None, Field(description='Display name of the vault item', title='ItemNameSchema')] = None
  notes: Annotated[str | None, Field(description='Free-form notes associated with the item', title='ItemNotesSchema')] = None
  favorite: Annotated[bool | None, Field(description='Whether the item is marked as a favorite', title='ItemFavoriteSchema')] = None
  fields: Annotated[Sequence[FieldSchema] | None, Field(description='Array of custom fields', title='ItemFieldsSchema')] = None
  login: Annotated[ItemLoginSchema | None, Field(description='Login-specific data (username, password, URIs, TOTP)')] = None
  secure_note: Annotated[ItemSecureNoteSchema | None, Field(alias='secureNote', description='Secure note data')] = None
  card: Annotated[ItemCardSchema | None, Field(description='Credit card data')] = None
  identity: Annotated[ItemIdentitySchema | None, Field(description='Identity data')] = None
  reprompt: Annotated[
    RepromptSchema | None,
    Field(description='Master password re-prompt requirement (0=none, 1=required)', title='RepromptSchema')] = None


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
