# module_template

"""Types for Bitwarden Send functionality."""

# imports_template

from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field

if TYPE_CHECKING:
  from .global_types import (Collection, CustomField, Folder, Group, Status, Uris)

if TYPE_CHECKING:
  from .item_types import (ItemCard, ItemIdentity, ItemLogin, ItemSecureNote, ItemTemplate)



# enum_template

class SendTemplateType(Enum):
  """Enumeration for type field values."""

  VALUE_0 = 0
  VALUE_1 = 1


# model_template

class SendTemplate(BaseModel):
  """SendTemplate model."""

  # property_template

  deletionDate: Optional[datetime]

  # property_template

  disabled: Optional[bool]

  # property_template

  expirationDate: Optional[datetime]

  # property_template

  file: Optional[str]

  # property_template

  hideEmail: Optional[bool]

  # property_template

  maxAccessCount: Optional[int]

  # property_template

  name: Optional[str]

  # property_template

  notes: Optional[str]

  # property_template

  password: Optional[str]

  # property_template

  text: Optional[Any]

  # property_template

  type: Optional[int]



# model_template

class SendText(BaseModel):
  """SendText model."""

  # property_template

  hidden: Optional[bool]

  # property_template

  text: Optional[str]


