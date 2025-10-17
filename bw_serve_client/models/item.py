# Bitwarden Vault Management API Models
# Generated from OpenAPI specification
# DO NOT EDIT MANUALLY

from __future__ import annotations

from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from . import Field, Uris


class Brand(Enum):
    visa = 'visa'


class Card(BaseModel):
    brand: Optional[Brand] = None
    cardholderName: Optional[str] = None
    code: Optional[str] = None
    expMonth: Optional[str] = None
    expYear: Optional[str] = None
    number: Optional[str] = None


class Identity(BaseModel):
    address1: Optional[str] = None
    address2: Optional[str] = None
    address3: Optional[str] = None
    city: Optional[str] = None
    company: Optional[str] = None
    country: Optional[str] = None
    email: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    licenseNumber: Optional[str] = None
    middleName: Optional[str] = None
    passportNumber: Optional[str] = None
    phone: Optional[str] = None
    postalCode: Optional[str] = None
    ssn: Optional[str] = None
    state: Optional[str] = None
    title: Optional[str] = None
    username: Optional[str] = None


class Type(Enum):
    integer_0 = 0


class SecureNote(BaseModel):
    type: Optional[Type] = None


class Reprompt(Enum):
    integer_0 = 0
    integer_1 = 1


class Type1Model(Enum):
    int_1 = 1
    int_2 = 2
    int_3 = 3
    int_4 = 4


class Login(BaseModel):
    password: Optional[str] = None
    totp: Optional[str] = None
    uris: Optional[Uris] = None
    username: Optional[str] = None


class Template(BaseModel):
    card: Optional[Card] = None
    collectionIds: Optional[List[UUID]] = None
    favorite: Optional[bool] = None
    fields: Optional[List[Field]] = None
    folderId: Optional[UUID] = None
    identity: Optional[Identity] = None
    login: Optional[Login] = None
    name: Optional[str] = None
    notes: Optional[str] = None
    organizationId: Optional[UUID] = None
    reprompt: Optional[Reprompt] = None
    secureNote: Optional[SecureNote] = None
    type: Optional[Type1Model] = None
