from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from datetime import date, datetime
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .global_types import Collection, Field, Folder, Group, Status, Uris

if TYPE_CHECKING:
    from .item_types import ItemCard, ItemIdentity, ItemLogin, ItemSecureNote, ItemTemplate


class SendTemplateType(Enum):
    VALUE_0 = 0
    VALUE_1 = 1

class SendTemplate(BaseModel):
    """SendTemplate model"""

    deletionDate: Optional[datetime]
    disabled: Optional[bool]
    expirationDate: Optional[datetime]
    file: Optional[str]
    hideEmail: Optional[bool]
    maxAccessCount: Optional[int]
    name: Optional[str]
    notes: Optional[str]
    password: Optional[str]
    text: Optional[Any]
    type: Optional[int]

class SendText(BaseModel):
    """SendText model"""

    hidden: Optional[bool]
    text: Optional[str]
