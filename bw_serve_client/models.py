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


class Type(Enum):
    """
    Type of vault item (1=login, 2=note, 3=card, 4=identity)
    """
    INTEGER_1 = 1
    INTEGER_2 = 2
    INTEGER_3 = 3
    INTEGER_4 = 4


class Reprompt(Enum):
    """
    Master password re-prompt requirement (0=none, 1=required)
    """
    INTEGER_0 = 0
    INTEGER_1 = 1


class ItemSecureNoteSchema(BaseModel):
    """
    Secure note data schema for vault items
    """
    model_config = ConfigDict(
        extra='forbid',
        populate_by_name=True,
    )
    type: Literal[0] | None
    """
    Secure note type (always 0)
    """


class ItemCardSchema(BaseModel):
    """
    Credit card data schema for vault items
    """
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
    """
    Identity data schema for vault items
    """
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
    """
    URI matching behavior (0=domain, 1=host, 2=startsWith, 3=exact, 4=regex, 5=never)
    """
    INTEGER_0 = 0
    INTEGER_1 = 1
    INTEGER_2 = 2
    INTEGER_3 = 3
    INTEGER_4 = 4
    INTEGER_5 = 5


class UrisSchema(BaseModel):
    """
    URI collection schema for login items
    """
    model_config = ConfigDict(
        extra='forbid',
        populate_by_name=True,
    )
    match: Match | None
    """
    URI matching behavior (0=domain, 1=host, 2=startsWith, 3=exact, 4=regex, 5=never)
    """
    uri: str | None
    """
    The URI/URL value
    """


class Type1(Enum):
    """
    Field type (0=text, 1=hidden, 2=boolean, 3=linked)
    """
    FIELD_0 = 0
    FIELD_1 = 1
    FIELD_2 = 2
    FIELD_3 = 3


class FieldSchema(BaseModel):
    """
    Custom field schema for vault items
    """
    model_config = ConfigDict(
        extra='forbid',
        populate_by_name=True,
    )
    name: str | None
    """
    Name of the custom field
    """
    value: str | None
    """
    Value of the custom field
    """
    type: Type1 | None
    """
    Field type (0=text, 1=hidden, 2=boolean, 3=linked)
    """


class FolderSchema(BaseModel):
    """
    Folder schema for organizing vault items
    """
    model_config = ConfigDict(
        extra='forbid',
        populate_by_name=True,
    )
    name: str | None
    """
    Name of the folder
    """


class Type2(Enum):
    """
    Type of Send (0=text, 1=file)
    """
    INTEGER_0 = 0
    INTEGER_1 = 1


class SendTextSchema(BaseModel):
    """
    Text content schema for Bitwarden Send items
    """
    model_config = ConfigDict(
        extra='forbid',
        populate_by_name=True,
    )
    text: str | None
    """
    Text content of the Send
    """
    hidden: bool | None
    """
    Whether the text is hidden by default
    """


class GroupSchema(BaseModel):
    """
    Group schema for user management
    """
    model_config = ConfigDict(
        extra='forbid',
        populate_by_name=True,
    )
    id: UUID | None
    read_only: Annotated[bool | None, Field(alias='readOnly')]
    hide_passwords: Annotated[bool | None, Field(alias='hidePasswords')]


class Status(Enum):
    LOCKED = 'locked'
    UNLOCKED = 'unlocked'
    UNAUTHENTICATED = 'unauthenticated'


class Template(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        populate_by_name=True,
    )
    server_url: Annotated[constr(pattern=r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]{0,61}[A-Za-z0-9])$') | None, Field(alias='serverUrl')]
    last_sync: Annotated[AwareDatetime | None, Field(alias='lastSync')]
    user_email: Annotated[EmailStr | None, Field(alias='userEmail')]
    user_id: Annotated[UUID | None, Field(alias='userID')]
    status: Status | None


class Data(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        populate_by_name=True,
    )
    object: Literal['template'] | None
    template: Template | None


class StatusSchema(BaseModel):
    """
    AGENT: fixme
    """
    model_config = ConfigDict(
        extra='forbid',
        populate_by_name=True,
    )
    success: bool | None
    data: Data | None


class Data1(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        populate_by_name=True,
    )
    no_color: Annotated[bool | None, Field(alias='noColor')]
    object: str | None
    title: str | None
    message: str | None


class LockUnlockSuccessSchema(BaseModel):
    """
    Success response schema for lock/unlock operations
    """
    model_config = ConfigDict(
        extra='forbid',
        populate_by_name=True,
    )
    success: bool | None
    data: Data1 | None


class DeviceApprovalPropertiesSchema(BaseModel):
    """
    Device approval properties schema for organization management
    """
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
    data: FolderSchema | None



ObjectFolderIdPutParameters = ObjectItemIdPutParameters





ObjectFolderIdPutResponse = ObjectFolderPostResponse





ObjectFolderIdGetParameters = ObjectItemIdPutParameters





ObjectFolderIdGetResponse = ObjectFolderPostResponse





ObjectFolderIdDeleteParameters = ObjectItemIdPutParameters





ObjectFolderIdDeleteResponse = ObjectItemIdDeleteResponse




class ListObjectFoldersGetParameters(BaseModel):
    search: str | None


class Data3(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        populate_by_name=True,
    )
    object: Literal['list'] | None
    data: List[FolderSchema] | None


class ListObjectFoldersGetResponse(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        populate_by_name=True,
    )
    success: bool | None
    data: Data3 | None



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


class Type3(Enum):
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
    type: Type3



DeviceApprovalOrganizationIdApproveRequestIdPostParameters = DeviceApprovalOrganizationIdDenyRequestIdPostParameters




class ItemLoginSchema(BaseModel):
    """
    Login-specific data schema for vault items
    """
    model_config = ConfigDict(
        extra='forbid',
        populate_by_name=True,
    )
    uris: UrisSchema | None
    """
    Array of URIs associated with this login
    """
    username: str | None
    """
    Username for the login
    """
    password: str | None
    """
    Password for the login
    """
    totp: str | None
    """
    TOTP secret for two-factor authentication
    """


class SendTemplateSchema(BaseModel):
    """
    Template schema for Bitwarden Send items
    """
    model_config = ConfigDict(
        extra='forbid',
        populate_by_name=True,
    )
    name: str | None
    """
    Name of the Send
    """
    notes: str | None
    """
    Notes for the Send
    """
    type: Type2 | None
    """
    Type of Send (0=text, 1=file)
    """
    text: SendTextSchema | None
    file: str | None
    max_access_count: Annotated[int | None, Field(alias='maxAccessCount')]
    deletion_date: Annotated[AwareDatetime | None, Field(alias='deletionDate')]
    expiration_date: Annotated[AwareDatetime | None, Field(alias='expirationDate')]
    password: str | None
    disabled: bool | None
    hide_email: Annotated[bool | None, Field(alias='hideEmail')]


class CollectionSchema(BaseModel):
    """
    Collection schema for organizing vault items
    """
    model_config = ConfigDict(
        extra='forbid',
        populate_by_name=True,
    )
    organization_id: Annotated[UUID | None, Field(alias='organizationId')]
    name: str | None
    external_id: Annotated[str | None, Field(alias='externalId')]
    groups: List[GroupSchema] | None


class DeviceApprovalListSchema(RootModel[List[DeviceApprovalPropertiesSchema]]):
    """
    Device approval list schema for organization management
    """
    model_config = ConfigDict(
        populate_by_name=True,
    )
    root: Annotated[List[DeviceApprovalPropertiesSchema], Field(title='DeviceApprovalListSchema')]
    """
    Device approval list schema for organization management
    """


class ObjectSendPostResponse(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        populate_by_name=True,
    )
    success: bool | None
    data: SendTemplateSchema | None



ObjectSendIdPutResponse = ObjectSendPostResponse





ObjectSendIdGetResponse = ObjectSendPostResponse




class Data4(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        populate_by_name=True,
    )
    object: Literal['list'] | None
    data: List[SendTemplateSchema] | None


class ListObjectSendGetResponse(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        populate_by_name=True,
    )
    success: bool | None
    data: Data4 | None



SendIdRemovePasswordPostResponse = ObjectSendPostResponse




class ItemTemplateSchema(BaseModel):
    """
    Template schema for vault items with all possible fields
    """
    model_config = ConfigDict(
        extra='forbid',
        populate_by_name=True,
    )
    organization_id: Annotated[UUID | None, Field(alias='organizationId')]
    """
    Organization ID if item belongs to an organization
    """
    collection_ids: Annotated[List[UUID] | None, Field(alias='collectionIds')]
    """
    Array of collection IDs for organization items
    """
    folder_id: Annotated[UUID | None, Field(alias='folderId')]
    """
    Folder ID for organizing the item
    """
    type: Type | None
    """
    Type of vault item (1=login, 2=note, 3=card, 4=identity)
    """
    name: str | None
    """
    Display name of the vault item
    """
    notes: str | None
    """
    Free-form notes associated with the item
    """
    favorite: bool | None
    """
    Whether the item is marked as a favorite
    """
    fields: List[FieldSchema] | None
    """
    Array of custom fields
    """
    login: ItemLoginSchema | None
    """
    Login-specific data (username, password, URIs, TOTP)
    """
    secure_note: Annotated[ItemSecureNoteSchema | None, Field(alias='secureNote')]
    """
    Secure note data
    """
    card: ItemCardSchema | None
    """
    Credit card data
    """
    identity: ItemIdentitySchema | None
    """
    Identity data
    """
    reprompt: Reprompt | None
    """
    Master password re-prompt requirement (0=none, 1=required)
    """


class ObjectItemPostResponse(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        populate_by_name=True,
    )
    success: bool | None
    data: ItemTemplateSchema | None
    revision_date: Annotated[AwareDatetime | None, Field(alias='revisionDate')]
    delete_date: Annotated[AwareDatetime | None, Field(alias='deleteDate')] = None



ObjectItemIdPutResponse = ObjectItemPostResponse





ObjectItemIdGetResponse = ObjectItemPostResponse




class Data2(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        populate_by_name=True,
    )
    object: Literal['list'] | None
    data: List[ItemTemplateSchema] | None


class ListObjectItemsGetResponse(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        populate_by_name=True,
    )
    success: bool | None
    data: Data2 | None
