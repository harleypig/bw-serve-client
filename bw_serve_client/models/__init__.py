# Bitwarden Vault Management API Models
# Generated from OpenAPI specification
# DO NOT EDIT MANUALLY

from __future__ import annotations

from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, EmailStr, constr


class Type(Enum):
    field_0 = 0
    field_1 = 1
    field_2 = 2
    field_3 = 3


class Field(BaseModel):
    name: Optional[str] = None
    type: Optional[Type] = None
    value: Optional[str] = None


class Folder(BaseModel):
    name: Optional[str] = None


class Group(BaseModel):
    hidePasswords: Optional[bool] = None
    id: Optional[UUID] = None
    readOnly: Optional[bool] = None


class Object(Enum):
    template = 'template'


class Status1(Enum):
    locked = 'locked'
    unlocked = 'unlocked'
    unauthenticated = 'unauthenticated'


class Template(BaseModel):
    lastSync: Optional[AwareDatetime] = None
    serverUrl: Optional[
        constr(
            pattern=r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]{0,61}[A-Za-z0-9])$'
        )
    ] = None
    status: Optional[Status1] = None
    userEmail: Optional[EmailStr] = None
    userID: Optional[UUID] = None


class Data(BaseModel):
    object: Optional[Object] = None
    template: Optional[Template] = None


class Status(BaseModel):
    data: Optional[Data] = None
    success: Optional[bool] = None


class Match(Enum):
    integer_0 = 0
    integer_1 = 1
    integer_2 = 2
    integer_3 = 3
    integer_4 = 4
    integer_5 = 5


class Uris(BaseModel):
    match: Optional[Match] = None
    uri: Optional[str] = None


class Collection(BaseModel):
    externalId: Optional[str] = None
    groups: Optional[List[Group]] = None
    name: Optional[str] = None
    organizationId: Optional[UUID] = None
