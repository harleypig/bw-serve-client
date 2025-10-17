# module_template

"""Types specific to vault items and templates."""

# imports_template

from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field

if TYPE_CHECKING:
  from .global_types import (Collection, CustomField, Folder, Group, Status, Uris)

if TYPE_CHECKING:
  from .send_types import SendTemplate, SendText



# enum_template

class ItemCardBrand(Enum):
  """Enumeration for brand field values."""

  VISA = 'visa'


# model_template

class ItemCard(BaseModel):
  """ItemCard model."""

  # property_template

  brand: Optional[str]

  # property_template

  cardholderName: Optional[str]

  # property_template

  code: Optional[str]

  # property_template

  expMonth: Optional[str]

  # property_template

  expYear: Optional[str]

  # property_template

  number: Optional[str]



# model_template

class ItemIdentity(BaseModel):
  """ItemIdentity model."""

  # property_template

  address1: Optional[str]

  # property_template

  address2: Optional[str]

  # property_template

  address3: Optional[str]

  # property_template

  city: Optional[str]

  # property_template

  company: Optional[str]

  # property_template

  country: Optional[str]

  # property_template

  email: Optional[str]

  # property_template

  firstName: Optional[str]

  # property_template

  lastName: Optional[str]

  # property_template

  licenseNumber: Optional[str]

  # property_template

  middleName: Optional[str]

  # property_template

  passportNumber: Optional[str]

  # property_template

  phone: Optional[str]

  # property_template

  postalCode: Optional[str]

  # property_template

  ssn: Optional[str]

  # property_template

  state: Optional[str]

  # property_template

  title: Optional[str]

  # property_template

  username: Optional[str]



# model_template

class ItemLogin(BaseModel):
  """ItemLogin model."""

  # property_template

  password: Optional[str]

  # property_template

  totp: Optional[str]

  # property_template

  uris: Optional[Any]

  # property_template

  username: Optional[str]



# enum_template

class ItemSecureNoteType(Enum):
  """Enumeration for type field values."""

  VALUE_0 = 0


# model_template

class ItemSecureNote(BaseModel):
  """ItemSecureNote model."""

  # property_template

  type: Optional[int]



# enum_template

class ItemTemplateReprompt(Enum):
  """Enumeration for reprompt field values."""

  VALUE_0 = 0
  VALUE_1 = 1


# enum_template

class ItemTemplateType(Enum):
  """Enumeration for type field values."""

  VALUE_0 = 1
  VALUE_1 = 2
  VALUE_2 = 3
  VALUE_3 = 4


# model_template

class ItemTemplate(BaseModel):
  """ItemTemplate model."""

  # property_template

  card: Optional[Any]

  # property_template

  collectionIds: Optional[List[UUID]]

  # property_template

  favorite: Optional[bool]

  # property_template

  fields: Optional[List["CustomField"]]

  # property_template

  folderId: Optional[UUID]

  # property_template

  identity: Optional[Any]

  # property_template

  login: Optional[Any]

  # property_template

  name: Optional[str]

  # property_template

  notes: Optional[str]

  # property_template

  organizationId: Optional[UUID]

  # property_template

  reprompt: Optional[int]

  # property_template

  secureNote: Optional[Any]

  # property_template

  type: Optional[int]


