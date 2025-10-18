# Bitwarden Vault Management API Models
# Generated from OpenAPI specification
# DO NOT EDIT MANUALLY


from __future__ import annotations

from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from . import Field
from . import Uris


class Brand(Enum):
    visa = 'visa'


class Card(BaseModel):
    brand: Optional[Brand]
    cardholderName: Optional[str]
    code: Optional[str]
    expMonth: Optional[str]
    expYear: Optional[str]
    number: Optional[str]


class Identity(BaseModel):
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


class Type(Enum):
    integer_0 = 0


class SecureNote(BaseModel):
    type: Optional[Type]


class Reprompt(Enum):
    integer_0 = 0
    integer_1 = 1


class Type1Model(Enum):
    int_1 = 1
    int_2 = 2
    int_3 = 3
    int_4 = 4


class Login(BaseModel):
    password: Optional[str]
    totp: Optional[str]
    uris: Optional[Uris]
    username: Optional[str]


class Template(BaseModel):
    card: Optional[Card]
    collectionIds: Optional[List[UUID]]
    favorite: Optional[bool]
    fields: Optional[List[Field]]
    folderId: Optional[UUID]
    identity: Optional[Identity]
    login: Optional[Login]
    name: Optional[str]
    notes: Optional[str]
    organizationId: Optional[UUID]
    reprompt: Optional[Reprompt]
    secureNote: Optional[SecureNote]
    type: Optional[Type1Model]
