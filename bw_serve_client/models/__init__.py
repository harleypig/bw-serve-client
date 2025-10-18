# Bitwarden Vault Management API Models
# Generated from OpenAPI specification
# DO NOT EDIT MANUALLY


from __future__ import annotations

from enum import Enum
from typing import Annotated, List, Optional
from uuid import UUID

from pydantic import AwareDatetime
from pydantic import BaseModel
from pydantic import constr
from pydantic import EmailStr
from pydantic import Field


class Type(Enum):
    field_0 = 0
    field_1 = 1
    field_2 = 2
    field_3 = 3


class FieldModel(BaseModel):
    name: Optional[str]
    type: Optional[Type]
    value: Optional[str]


class Folder(BaseModel):
    name: Optional[str]


class Group(BaseModel):
    hide_passwords: Annotated[Optional[bool], Field(alias='hidePasswords')]
    id: Optional[UUID]
    read_only: Annotated[Optional[bool], Field(alias='readOnly')]


class Object(Enum):
    template = 'template'


class Status1(Enum):
    locked = 'locked'
    unlocked = 'unlocked'
    unauthenticated = 'unauthenticated'


class Template(BaseModel):
    last_sync: Annotated[Optional[AwareDatetime], Field(alias='lastSync')]
    server_url: Annotated[Optional[constr(pattern=r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]{0,61}[A-Za-z0-9])$')], Field(alias='serverUrl')]
    status: Optional[Status1]
    user_email: Annotated[Optional[EmailStr], Field(alias='userEmail')]
    user_id: Annotated[Optional[UUID], Field(alias='userID')]


class Data(BaseModel):
    object: Optional[Object]
    template: Optional[Template]


class Status(BaseModel):
    data: Optional[Data]
    success: Optional[bool]


class Match(Enum):
    integer_0 = 0
    integer_1 = 1
    integer_2 = 2
    integer_3 = 3
    integer_4 = 4
    integer_5 = 5


class Uris(BaseModel):
    match: Optional[Match]
    uri: Optional[str]


class Collection(BaseModel):
    external_id: Annotated[Optional[str], Field(alias='externalId')]
    groups: Optional[List[Group]]
    name: Optional[str]
    organization_id: Annotated[Optional[UUID], Field(alias='organizationId')]
