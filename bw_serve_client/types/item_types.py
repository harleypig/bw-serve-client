from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from datetime import date, datetime
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .global_types import Collection, Field, Folder, Group, Status, Uris

if TYPE_CHECKING:
    from .send_types import SendTemplate, SendText


class ItemCardBrand(Enum):
    VISA = 'visa'

class ItemCard(BaseModel):
    """ItemCard model"""

    brand: Optional[str]
    cardholderName: Optional[str]
    code: Optional[str]
    expMonth: Optional[str]
    expYear: Optional[str]
    number: Optional[str]

class ItemIdentity(BaseModel):
    """ItemIdentity model"""

    address1: Optional[str]
    address2: Optional[str]
    address3: Optional[str]
    city: Optional[str]
    company: Optional[str]
    country: Optional[str]
    email: Optional[str]
    firstName: Optional[str]
    lastName: Optional[str]
    licenseNumber: Optional[str]
    middleName: Optional[str]
    passportNumber: Optional[str]
    phone: Optional[str]
    postalCode: Optional[str]
    ssn: Optional[str]
    state: Optional[str]
    title: Optional[str]
    username: Optional[str]

class ItemLogin(BaseModel):
    """ItemLogin model"""

    password: Optional[str]
    totp: Optional[str]
    uris: Optional[Any]
    username: Optional[str]

class ItemSecureNoteType(Enum):
    VALUE_0 = 0

class ItemSecureNote(BaseModel):
    """ItemSecureNote model"""

    type: Optional[int]

class ItemTemplateReprompt(Enum):
    VALUE_0 = 0
    VALUE_1 = 1
class ItemTemplateType(Enum):
    VALUE_0 = 1
    VALUE_1 = 2
    VALUE_2 = 3
    VALUE_3 = 4

class ItemTemplate(BaseModel):
    """ItemTemplate model"""

    card: Optional[Any]
    collectionIds: Optional[List[UUID]]
    favorite: Optional[bool]
    fields: Optional[List["Field"]]
    folderId: Optional[UUID]
    identity: Optional[Any]
    login: Optional[Any]
    name: Optional[str]
    notes: Optional[str]
    organizationId: Optional[UUID]
    reprompt: Optional[int]
    secureNote: Optional[Any]
    type: Optional[int]
