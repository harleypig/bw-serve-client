# module_template

"""Global types used across multiple API endpoints."""

# imports_template

from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field

if TYPE_CHECKING:
  from .item_types import (ItemCard, ItemIdentity, ItemLogin, ItemSecureNote, ItemTemplate)

if TYPE_CHECKING:
  from .send_types import SendTemplate, SendText




# model_template

class Collection(BaseModel):
  """Collection model."""

  # property_template

  externalId: Optional[str]

  # property_template

  groups: Optional[List["Group"]]

  # property_template

  name: Optional[str]

  # property_template

  organizationId: Optional[UUID]



# enum_template

class CustomFieldType(Enum):
  """Enumeration for type field values."""

  VALUE_0 = 0
  VALUE_1 = 1
  VALUE_2 = 2
  VALUE_3 = 3


# model_template

class CustomField(BaseModel):
  """CustomField model."""

  # property_template

  name: Optional[str]

  # property_template

  type: Optional[int]

  # property_template

  value: Optional[str]



# model_template

class Folder(BaseModel):
  """Folder model."""

  # property_template

  name: Optional[str]



# model_template

class Group(BaseModel):
  """Group model."""

  # property_template

  hidePasswords: Optional[bool]

  # property_template

  id: Optional[UUID]

  # property_template

  readOnly: Optional[bool]



# model_template

class Status(BaseModel):
  """Status model."""

  # property_template

  data: Optional[Dict[str, Any]]

  # property_template

  success: Optional[bool]



# enum_template

class UrisMatch(Enum):
  """Enumeration for match field values."""

  VALUE_0 = 0
  VALUE_1 = 1
  VALUE_2 = 2
  VALUE_3 = 3
  VALUE_4 = 4
  VALUE_5 = 5


# model_template

class Uris(BaseModel):
  """Uris model."""

  # property_template

  match: Optional[int]

  # property_template

  uri: Optional[str]


