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


class SecureNote(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  type: Literal[0] | None
  """Secure note type (always 0)."""


class Card(BaseModel):
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


class Identity(BaseModel):
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


class Login(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  uris: Uris | None
  """Array of URIs associated with this login."""
  username: str | None
  """Username for the login."""
  password: str | None
  """Password for the login."""
  totp: str | None
  """TOTP secret for two-factor authentication."""


class Template(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  organization_id: Annotated[UUID | None, Field(alias='organizationId')]
  """Organization ID if item belongs to an organization."""
  collection_ids: Annotated[List[UUID] | None, Field(alias='collectionIds')]
  """Array of collection IDs for organization items."""
  folder_id: Annotated[UUID | None, Field(alias='folderId')]
  """Folder ID for organizing the item."""
  type: Type | None
  """Type of vault item (1=login, 2=note, 3=card, 4=identity)."""
  name: str | None
  """Display name of the vault item."""
  notes: str | None
  """Free-form notes associated with the item."""
  favorite: bool | None
  """Whether the item is marked as a favorite."""
  fields: List[FieldModel] | None
  """Array of custom fields."""
  login: Login | None
  """Login-specific data (username, password, URIs, TOTP)."""
  secure_note: Annotated[SecureNote | None, Field(alias='secureNote')]
  """Secure note data."""
  card: Card | None
  """Credit card data."""
  identity: Identity | None
  """Identity data."""
  reprompt: Reprompt | None
  """Master password re-prompt requirement (0=none, 1=required)."""
