# Bitwarden Vault Management API Models
# Generated from OpenAPI specification
# DO NOT EDIT MANUALLY

from __future__ import annotations

from enum import Enum
from typing import Annotated, List, Literal
from uuid import UUID

from pydantic import AnyUrl
from pydantic import AwareDatetime
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import constr
from pydantic import EmailStr
from pydantic import Field
from pydantic import RootModel

from . import item
from . import send


class Match(Enum):
  """URI matching behavior (0=domain, 1=host, 2=startsWith, 3=exact, 4=regex, 5=never)."""
  INTEGER_0 = 0
  INTEGER_1 = 1
  INTEGER_2 = 2
  INTEGER_3 = 3
  INTEGER_4 = 4
  INTEGER_5 = 5


class Uris(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  match: Match | None
  """URI matching behavior (0=domain, 1=host, 2=startsWith, 3=exact, 4=regex, 5=never)."""
  uri: str | None
  """The URI/URL value."""


class Type(Enum):
  """Field type (0=text, 1=hidden, 2=boolean, 3=linked)."""
  FIELD_0 = 0
  FIELD_1 = 1
  FIELD_2 = 2
  FIELD_3 = 3


class FieldModel(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  name: str | None
  """Name of the custom field."""
  value: str | None
  """Value of the custom field."""
  type: Type | None
  """Field type (0=text, 1=hidden, 2=boolean, 3=linked)."""


class Folder(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  name: str | None
  """Name of the folder."""


class Group(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  id: UUID | None
  read_only: Annotated[bool | None, Field(alias='readOnly')]
  hide_passwords: Annotated[bool | None, Field(alias='hidePasswords')]


class Status1(Enum):
  LOCKED = 'locked'
  UNLOCKED = 'unlocked'
  UNAUTHENTICATED = 'unauthenticated'


class Template(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  server_url: Annotated[constr(
    pattern=
    r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]{0,61}[A-Za-z0-9])$'
  ) | None,
                        Field(alias='serverUrl')]
  last_sync: Annotated[AwareDatetime | None, Field(alias='lastSync')]
  user_email: Annotated[EmailStr | None, Field(alias='userEmail')]
  user_id: Annotated[UUID | None, Field(alias='userID')]
  status: Status1 | None


class Data(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  object: Literal['template'] | None
  template: Template | None


class Status(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  success: bool | None
  data: Data | None


class Deviceapprovalproperties(BaseModel):
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


class UnlockPostRequest(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  password: str | None


class ObjectItemIdPutParameters(BaseModel):
  id: UUID


ObjectItemIdGetParameters = ObjectItemIdPutParameters

ObjectItemIdDeleteParameters = ObjectItemIdPutParameters


class ObjectItemIdDeleteResponse(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  success: bool | None


RestoreItemIdPostParameters = ObjectItemIdPutParameters

RestoreItemIdPostResponse = ObjectItemIdDeleteResponse


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


class ObjectFolderPostResponse(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  success: bool | None
  data: Folder | None


ObjectFolderIdPutParameters = ObjectItemIdPutParameters

ObjectFolderIdPutResponse = ObjectFolderPostResponse

ObjectFolderIdGetParameters = ObjectItemIdPutParameters

ObjectFolderIdGetResponse = ObjectFolderPostResponse

ObjectFolderIdDeleteParameters = ObjectItemIdPutParameters

ObjectFolderIdDeleteResponse = ObjectItemIdDeleteResponse


class ListObjectFoldersGetParameters(BaseModel):
  search: str | None


class Data2(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  object: Literal['list'] | None
  data: List[Folder] | None


class ListObjectFoldersGetResponse(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  success: bool | None
  data: Data2 | None


ObjectSendIdPutParameters = ObjectItemIdPutParameters

ObjectSendIdGetParameters = ObjectItemIdPutParameters

ObjectSendIdDeleteParameters = ObjectItemIdPutParameters

ObjectSendIdDeleteResponse = ObjectItemIdDeleteResponse

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
  array: List | None


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


class Collection(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  organization_id: Annotated[UUID | None, Field(alias='organizationId')]
  name: str | None
  external_id: Annotated[str | None, Field(alias='externalId')]
  groups: List[Group] | None


class Deviceapprovallist(RootModel[List[Deviceapprovalproperties]]):
  model_config = ConfigDict(populate_by_name=True,)
  root: List[Deviceapprovalproperties]


class ObjectSendPostResponse(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  success: bool | None
  data: send.Template | None


ObjectSendIdPutResponse = ObjectSendPostResponse

ObjectSendIdGetResponse = ObjectSendPostResponse


class Data3(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  object: Literal['list'] | None
  data: List[send.Template] | None


class ListObjectSendGetResponse(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  success: bool | None
  data: Data3 | None


SendIdRemovePasswordPostResponse = ObjectSendPostResponse


class ObjectItemPostResponse(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  success: bool | None
  data: item.Template | None
  revision_date: Annotated[AwareDatetime | None, Field(alias='revisionDate')]
  delete_date: Annotated[AwareDatetime | None, Field(alias='deleteDate')] = None


ObjectItemIdPutResponse = ObjectItemPostResponse

ObjectItemIdGetResponse = ObjectItemPostResponse

ListObjectItemsGetResponse = ListObjectSendGetResponse
