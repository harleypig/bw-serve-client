# module_template

"""API response wrapper types."""

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

if TYPE_CHECKING:
  from .send_types import SendTemplate, SendText



# model_template

class LockUnlockSuccess(BaseModel):
  """LockUnlockSuccess model."""

  # property_template

  data: Optional[Dict[str, Any]]

  # property_template

  success: Optional[bool]


