from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from datetime import date, datetime
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field

if TYPE_CHECKING:
  from .item_types import (ItemCard, ItemIdentity, ItemLogin, ItemSecureNote, ItemTemplate)

if TYPE_CHECKING:
  from .send_types import SendTemplate, SendText


class Collection(BaseModel):
  """Collection model"""

  externalId: Optional[str]
  groups: Optional[List["Group"]]
  name: Optional[str]
  organizationId: Optional[UUID]


class CustomFieldType(Enum):
  VALUE_0 = 0
  VALUE_1 = 1
  VALUE_2 = 2
  VALUE_3 = 3


class CustomField(BaseModel):
  """CustomField model"""

  name: Optional[str]
  type: Optional[int]
  value: Optional[str]


class Folder(BaseModel):
  """Folder model"""

  name: Optional[str]


class Group(BaseModel):
  """Group model"""

  hidePasswords: Optional[bool]
  id: Optional[UUID]
  readOnly: Optional[bool]


class Status(BaseModel):
  """Status model"""

  data: Optional[Dict[str, Any]]
  success: Optional[bool]


class UrisMatch(Enum):
  VALUE_0 = 0
  VALUE_1 = 1
  VALUE_2 = 2
  VALUE_3 = 3
  VALUE_4 = 4
  VALUE_5 = 5


class Uris(BaseModel):
  """Uris model"""

  match: Optional[int]
  uri: Optional[str]
