# Bitwarden Vault Management API Models
# Generated from OpenAPI specification
# DO NOT EDIT MANUALLY

from __future__ import annotations

from enum import Enum
from typing import Annotated, List, Optional
from uuid import UUID

from pydantic import AwareDatetime
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import constr
from pydantic import EmailStr
from pydantic import Field


class Collection(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  external_id: Annotated[Optional[str], Field(alias='externalId')]
  groups: Optional[List[Group]]
  name: Optional[str]
  organization_id: Annotated[Optional[UUID], Field(alias='organizationId')]


class Data(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  object: Optional[Object]
  template: Optional[Template]


class FieldModel(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  name: Optional[str]
  type: Optional[Type]
  value: Optional[str]


class Folder(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  name: Optional[str]


class Group(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  hide_passwords: Annotated[Optional[bool], Field(alias='hidePasswords')]
  id: Optional[UUID]
  read_only: Annotated[Optional[bool], Field(alias='readOnly')]


class Match(Enum):
  integer_0 = 0
  integer_1 = 1
  integer_2 = 2
  integer_3 = 3
  integer_4 = 4
  integer_5 = 5


class Object(Enum):
  template = 'template'


class Status(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  data: Optional[Data]
  success: Optional[bool]


class Status1(Enum):
  locked = 'locked'
  unlocked = 'unlocked'
  unauthenticated = 'unauthenticated'


class Template(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  last_sync: Annotated[Optional[AwareDatetime], Field(alias='lastSync')]
  server_url: Annotated[Optional[constr(
    pattern=
    r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]{0,61}[A-Za-z0-9])$'
  )],
                        Field(alias='serverUrl')]
  status: Optional[Status1]
  user_email: Annotated[Optional[EmailStr], Field(alias='userEmail')]
  user_id: Annotated[Optional[UUID], Field(alias='userID')]


class Type(Enum):
  field_0 = 0
  field_1 = 1
  field_2 = 2
  field_3 = 3


class Uris(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  match: Optional[Match]
  uri: Optional[str]
