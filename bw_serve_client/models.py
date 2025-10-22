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
  type: Annotated[Literal[0] | None, Field(description='Secure note type (always 0)')]


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
  match: Annotated[
    Match | None,
    Field(
      description=
      'URI matching behavior (0=domain, 1=host, 2=startsWith, 3=exact, 4=regex, 5=never)'
    )]
  uri: Annotated[str | None, Field(description='The URI/URL value')]


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
  name: Annotated[str | None, Field(description='Name of the custom field')]
  value: Annotated[str | None, Field(description='Value of the custom field')]
  type: Annotated[FieldTypeEnum | None,
                  Field(
                    description='Field type (0=text, 1=hidden, 2=boolean, 3=linked)',
                    title='FieldTypeEnum'
                  )]


class FolderSchema(BaseModel):
  """Folder schema for organizing vault items."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  name: Annotated[str | None, Field(description='Name of the folder')]


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
  status: Annotated[
    StatusEnum | None,
    Field(
      description='Vault status (locked, unlocked, or unauthenticated)', title='StatusEnum'
    )]


class StatusDataSchema(BaseModel):
  """Status response data containing template information."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  object: Literal['template'] | None
  template: Annotated[
    TemplateSchema | None,
    Field(
      description='Vault template schema containing server URL, sync info, and user details',
      title='TemplateSchema'
    )]


class StatusSchema(BaseModel):
  """AGENT: fixme."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  success: bool | None
  data: Annotated[StatusDataSchema | None,
                  Field(
                    description='Status response data containing template information',
                    title='StatusDataSchema'
                  )]


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
  data: Annotated[
    LockUnlockDataSchema | None,
    Field(
      description=
      'Data schema for lock/unlock response containing status message and display options',
      title='LockUnlockDataSchema'
    )]


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
  id: UUID


ObjectItemIdGetParameters = ObjectItemIdPutParameters

ObjectItemIdDeleteParameters = ObjectItemIdPutParameters

RestoreItemIdPostParameters = ObjectItemIdPutParameters


class ListObjectItemsGetParameters(BaseModel):
  organization_id: Annotated[UUID | None, Field(alias='organizationId')]
  collection_id: Annotated[UUID | None, Field(alias='collectionId')]
  folderid: UUID | None
  url: AnyUrl | None
  trash: bool | None
  search: str | None


class AttachmentPostParameters(BaseModel):
  itemid: UUID


class AttachmentPostRequest(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  file: bytes | None


class ObjectAttachmentIdGetParameters(BaseModel):
  id: UUID
  itemid: UUID


ObjectAttachmentIdDeleteParameters = ObjectAttachmentIdGetParameters

ObjectUsernameIdGetParameters = ObjectItemIdPutParameters

ObjectPasswordIdGetParameters = ObjectItemIdPutParameters

ObjectUriIdGetParameters = ObjectItemIdPutParameters

ObjectTotpIdGetParameters = ObjectItemIdPutParameters

ObjectNotesIdGetParameters = ObjectItemIdPutParameters

ObjectExposedIdGetParameters = ObjectItemIdPutParameters

ObjectFolderIdPutParameters = ObjectItemIdPutParameters

ObjectFolderIdGetParameters = ObjectItemIdPutParameters

ObjectFolderIdDeleteParameters = ObjectItemIdPutParameters


class ListObjectFoldersGetParameters(BaseModel):
  search: str | None


ObjectSendIdPutParameters = ObjectItemIdPutParameters

ObjectSendIdGetParameters = ObjectItemIdPutParameters

ObjectSendIdDeleteParameters = ObjectItemIdPutParameters

ListObjectSendGetParameters = ListObjectFoldersGetParameters

SendIdRemovePasswordPostParameters = ObjectItemIdPutParameters


class MoveItemidOrganizationIdPostParameters(BaseModel):
  itemid: UUID
  organization_id: Annotated[UUID, Field(alias='organizationId')]


class MoveItemidOrganizationIdPostRequest(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  array: Sequence[str] | None


class ObjectOrgCollectionPostParameters(BaseModel):
  organization_id: Annotated[UUID, Field(alias='organizationId')]


class ObjectOrgCollectionIdPutParameters(BaseModel):
  id: UUID
  organization_id: Annotated[UUID, Field(alias='organizationId')]


ObjectOrgCollectionIdGetParameters = ObjectOrgCollectionIdPutParameters

ObjectOrgCollectionIdDeleteParameters = ObjectOrgCollectionIdPutParameters


class ListObjectOrgCollectionsGetParameters(BaseModel):
  organization_id: Annotated[UUID, Field(alias='organizationId')]
  search: str | None


ListObjectCollectionsGetParameters = ListObjectFoldersGetParameters

ListObjectOrganizationsGetParameters = ListObjectFoldersGetParameters

ListObjectOrgMembersGetParameters = ObjectOrgCollectionPostParameters

ConfirmOrgMemberIdPostParameters = ObjectOrgCollectionIdPutParameters

DeviceApprovalOrganizationIdGetParameters = ObjectOrgCollectionPostParameters

DeviceApprovalOrganizationIdApproveAllPostParameters = ObjectOrgCollectionPostParameters


class DeviceApprovalOrganizationIdDenyRequestIdPostParameters(BaseModel):
  organization_id: Annotated[UUID, Field(alias='organizationId')]
  request_id: Annotated[UUID, Field(alias='request-id')]


DeviceApprovalOrganizationIdDenyAllPostParameters = ObjectOrgCollectionPostParameters


class GenerateGetParameters(BaseModel):
  length: int | None
  uppercase: bool | None
  lowercase: bool | None
  number: bool | None
  special: bool | None
  passphrase: bool | None
  words: int | None
  separator: str | None
  capitalize: bool | None
  include_number: Annotated[bool | None, Field(alias='includeNumber')]


class Type1(Enum):
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
  type: Type1


DeviceApprovalOrganizationIdApproveRequestIdPostParameters = DeviceApprovalOrganizationIdDenyRequestIdPostParameters


class ItemLoginSchema(BaseModel):
  """Login-specific data schema for vault items."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  uris: Annotated[UrisSchema | None,
                  Field(description='Array of URIs associated with this login')]
  username: Annotated[str | None, Field(description='Username for the login')]
  password: Annotated[str | None, Field(description='Password for the login')]
  totp: Annotated[str | None,
                  Field(description='TOTP secret for two-factor authentication')]


class SendTemplateSchema(BaseModel):
  """Template schema for Bitwarden Send items."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  name: Annotated[str | None, Field(description='Name of the Send')]
  notes: Annotated[str | None, Field(description='Notes for the Send')]
  type: Annotated[SendTypeEnum | None,
                  Field(description='Type of Send (0=text, 1=file)', title='SendTypeEnum')]
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
                  Field(
                    description='Device approval list schema for organization management',
                    title='DeviceApprovalListSchema'
                  )]


class ItemTemplateSchema(BaseModel):
  """Template schema for vault items with all possible fields."""
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  organization_id: Annotated[
    UUID | None,
    Field(
      alias='organizationId',
      description='Organization ID if item belongs to an organization'
    )]
  collection_ids: Annotated[
    Sequence[UUID] | None,
    Field(
      alias='collectionIds', description='Array of collection IDs for organization items'
    )]
  folder_id: Annotated[
    UUID | None,
    Field(alias='folderId', description='Folder ID for organizing the item')]
  type: Annotated[
    Type | None,
    Field(description='Type of vault item (1=login, 2=note, 3=card, 4=identity)')]
  name: Annotated[str | None, Field(description='Display name of the vault item')]
  notes: Annotated[str | None,
                   Field(description='Free-form notes associated with the item')]
  favorite: Annotated[bool | None,
                      Field(description='Whether the item is marked as a favorite')]
  fields: Annotated[Sequence[FieldSchema] | None,
                    Field(description='Array of custom fields')]
  login: Annotated[
    ItemLoginSchema | None,
    Field(description='Login-specific data (username, password, URIs, TOTP)')]
  secure_note: Annotated[ItemSecureNoteSchema | None,
                         Field(alias='secureNote', description='Secure note data')]
  card: Annotated[ItemCardSchema | None, Field(description='Credit card data')]
  identity: Annotated[ItemIdentitySchema | None, Field(description='Identity data')]
  reprompt: Annotated[
    Reprompt | None,
    Field(description='Master password re-prompt requirement (0=none, 1=required)')]
