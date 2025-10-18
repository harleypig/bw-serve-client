# Bitwarden Vault Management API Models
# Generated from OpenAPI specification
# DO NOT EDIT MANUALLY

from __future__ import annotations

from enum import Enum
from typing import Annotated, List, Literal
from uuid import UUID

from pydantic import AwareDatetime
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import constr
from pydantic import EmailStr
from pydantic import Field


class AttachmentPostParameters(BaseModel):
  id: UUID


class AttachmentPostRequest(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  file: bytes | None


class Collection(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  external_id: Annotated[str | None, Field(alias='externalId')]
  groups: List[Group] | None
  name: str | None
  organization_id: Annotated[UUID | None, Field(alias='organizationId')]


class ConfirmOrgMemberIdPostParameters(BaseModel):
  id: UUID
  organization_id: Annotated[UUID, Field(alias='organizationId')]


class Data(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  object: Literal['template'] | None
  template: Template | None


class FieldModel(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  name: str | None
  type: Type | None
  value: str | None


class Folder(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  name: str | None


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


class Group(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  hide_passwords: Annotated[bool | None, Field(alias='hidePasswords')]
  id: UUID | None
  read_only: Annotated[bool | None, Field(alias='readOnly')]


class ListObjectCollectionsGetParameters(BaseModel):
  search: str | None


ListObjectFoldersGetParameters = ListObjectCollectionsGetParameters


class ListObjectItemsGetParameters(BaseModel):
  organization_id: Annotated[UUID | None, Field(alias='organizationId')]
  collection_id: Annotated[UUID | None, Field(alias='collectionId')]
  folderid: UUID | None
  url: str | None
  trash: bool | None
  search: str | None


class ListObjectOrgCollectionsGetParameters(BaseModel):
  organization_id: Annotated[UUID, Field(alias='organizationId')]
  search: str | None


class ListObjectOrgMembersGetParameters(BaseModel):
  organization_id: Annotated[UUID, Field(alias='organizationId')]


ListObjectOrganizationsGetParameters = ListObjectCollectionsGetParameters

ListObjectSendGetParameters = ListObjectCollectionsGetParameters


class Match(Enum):
  INTEGER_0 = 0
  INTEGER_1 = 1
  INTEGER_2 = 2
  INTEGER_3 = 3
  INTEGER_4 = 4
  INTEGER_5 = 5


class MoveItemidOrganizationIdPostParameters(BaseModel):
  itemid: UUID
  organization_id: Annotated[UUID, Field(alias='organizationId')]


class MoveItemidOrganizationIdPostRequest(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  array: List | None


class ObjectAttachmentIdDeleteParameters(BaseModel):
  id: UUID
  itemid: UUID


ObjectAttachmentIdGetParameters = ObjectAttachmentIdDeleteParameters

ObjectExposedIdGetParameters = AttachmentPostParameters

ObjectFolderIdDeleteParameters = AttachmentPostParameters

ObjectFolderIdGetParameters = AttachmentPostParameters

ObjectFolderIdPutParameters = AttachmentPostParameters

ObjectItemIdDeleteParameters = AttachmentPostParameters

ObjectItemIdGetParameters = AttachmentPostParameters

ObjectItemIdPutParameters = AttachmentPostParameters

ObjectNotesIdGetParameters = AttachmentPostParameters

ObjectOrgCollectionIdDeleteParameters = ConfirmOrgMemberIdPostParameters

ObjectOrgCollectionIdGetParameters = ConfirmOrgMemberIdPostParameters

ObjectOrgCollectionIdPutParameters = ConfirmOrgMemberIdPostParameters

ObjectOrgCollectionPostParameters = ListObjectOrgMembersGetParameters

ObjectPasswordIdGetParameters = AttachmentPostParameters

ObjectSendIdDeleteParameters = AttachmentPostParameters

ObjectSendIdGetParameters = AttachmentPostParameters

ObjectSendIdPutParameters = AttachmentPostParameters


class ObjectTemplateTypeGetParameters(BaseModel):
  type: Type1


ObjectTotpIdGetParameters = AttachmentPostParameters

ObjectUriIdGetParameters = AttachmentPostParameters

ObjectUsernameIdGetParameters = AttachmentPostParameters

RestoreItemIdPostParameters = AttachmentPostParameters

SendIdRemovePasswordPostParameters = AttachmentPostParameters


class Status(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  data: Data | None
  success: bool | None


class Status1(Enum):
  LOCKED = 'locked'
  UNLOCKED = 'unlocked'
  UNAUTHENTICATED = 'unauthenticated'


class Template(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  last_sync: Annotated[AwareDatetime | None, Field(alias='lastSync')]
  server_url: Annotated[constr(
    pattern=
    r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]{0,61}[A-Za-z0-9])$'
  ) | None,
                        Field(alias='serverUrl')]
  status: Status1 | None
  user_email: Annotated[EmailStr | None, Field(alias='userEmail')]
  user_id: Annotated[UUID | None, Field(alias='userID')]


class Type(Enum):
  FIELD_0 = 0
  FIELD_1 = 1
  FIELD_2 = 2
  FIELD_3 = 3


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


class UnlockPostRequest(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  password: str | None


class Uris(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  match: Match | None
  uri: str | None
