# Bitwarden Vault Management API Models
# Generated from OpenAPI specification
# DO NOT EDIT MANUALLY

from __future__ import annotations

from enum import Enum
from typing import Annotated, List, Literal
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
  brand: Literal['visa'] | None
  cardholder_name: Annotated[str | None, Field(alias='cardholderName')]
  code: str | None
  exp_month: Annotated[str | None, Field(alias='expMonth')]
  exp_year: Annotated[str | None, Field(alias='expYear')]
  number: str | None


class Identity(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  address1: str | None
  address2: str | None
  address3: str | None
  city: str | None
  company: str | None
  country: str | None
  email: str | None
  first_name: Annotated[str | None, Field(alias='firstName')]
  last_name: Annotated[str | None, Field(alias='lastName')]
  license_number: Annotated[str | None, Field(alias='licenseNumber')]
  middle_name: Annotated[str | None, Field(alias='middleName')]
  passport_number: Annotated[str | None, Field(alias='passportNumber')]
  phone: str | None
  postal_code: Annotated[str | None, Field(alias='postalCode')]
  ssn: str | None
  state: str | None
  title: str | None
  username: str | None


class Login(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  password: str | None
  totp: str | None
  uris: Uris | None
  username: str | None


class Reprompt(Enum):
  INTEGER_0 = 0
  INTEGER_1 = 1


class SecureNote(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  type: Literal[0] | None


class Template(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  card: Card | None
  collection_ids: Annotated[List[UUID] | None, Field(alias='collectionIds')]
  favorite: bool | None
  fields: List[FieldModel] | None
  folder_id: Annotated[UUID | None, Field(alias='folderId')]
  identity: Identity | None
  login: Login | None
  name: str | None
  notes: str | None
  organization_id: Annotated[UUID | None, Field(alias='organizationId')]
  reprompt: Reprompt | None
  secure_note: Annotated[SecureNote | None, Field(alias='secureNote')]
  type: Type | None


class Type(Enum):
  INT_1 = 1
  INT_2 = 2
  INT_3 = 3
  INT_4 = 4
