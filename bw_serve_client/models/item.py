# Bitwarden Vault Management API Models
# Generated from OpenAPI specification
# DO NOT EDIT MANUALLY

from __future__ import annotations

from enum import Enum
from typing import Annotated, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from . import FieldModel
from . import Uris


class Card(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  brand: Optional[Literal['visa']]
  cardholder_name: Annotated[Optional[str], Field(alias='cardholderName')]
  code: Optional[str]
  exp_month: Annotated[Optional[str], Field(alias='expMonth')]
  exp_year: Annotated[Optional[str], Field(alias='expYear')]
  number: Optional[str]


class Identity(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  address1: Optional[str]
  address2: Optional[str]
  address3: Optional[str]
  city: Optional[str]
  company: Optional[str]
  country: Optional[str]
  email: Optional[str]
  first_name: Annotated[Optional[str], Field(alias='firstName')]
  last_name: Annotated[Optional[str], Field(alias='lastName')]
  license_number: Annotated[Optional[str], Field(alias='licenseNumber')]
  middle_name: Annotated[Optional[str], Field(alias='middleName')]
  passport_number: Annotated[Optional[str], Field(alias='passportNumber')]
  phone: Optional[str]
  postal_code: Annotated[Optional[str], Field(alias='postalCode')]
  ssn: Optional[str]
  state: Optional[str]
  title: Optional[str]
  username: Optional[str]


class Login(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  password: Optional[str]
  totp: Optional[str]
  uris: Optional[Uris]
  username: Optional[str]


class Reprompt(Enum):
  INTEGER_0 = 0
  INTEGER_1 = 1


class SecureNote(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  type: Optional[Literal[0]]


class Template(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  card: Optional[Card]
  collection_ids: Annotated[Optional[List[UUID]], Field(alias='collectionIds')]
  favorite: Optional[bool]
  fields: Optional[List[FieldModel]]
  folder_id: Annotated[Optional[UUID], Field(alias='folderId')]
  identity: Optional[Identity]
  login: Optional[Login]
  name: Optional[str]
  notes: Optional[str]
  organization_id: Annotated[Optional[UUID], Field(alias='organizationId')]
  reprompt: Optional[Reprompt]
  secure_note: Annotated[Optional[SecureNote], Field(alias='secureNote')]
  type: Optional[Type]


class Type(Enum):
  INT_1 = 1
  INT_2 = 2
  INT_3 = 3
  INT_4 = 4
