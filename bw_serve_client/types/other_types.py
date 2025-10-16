from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from datetime import date, datetime
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field

if TYPE_CHECKING:
  from .global_types import Collection, CustomField, Folder, Group, Status, Uris

if TYPE_CHECKING:
  from .item_types import (ItemCard, ItemIdentity, ItemLogin, ItemSecureNote, ItemTemplate)

if TYPE_CHECKING:
  from .send_types import SendTemplate, SendText
