# Bitwarden Vault Management API Models
# Generated from OpenAPI specification
# DO NOT EDIT MANUALLY


from __future__ import annotations

from enum import Enum
from typing import Annotated, List, Optional
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field

from . import FieldModel
from . import Uris


class Brand(Enum):
    visa = 'visa'


class Card(BaseModel):
    brand: Optional[Brand]
    cardholder_name: Annotated[Optional[str], Field(alias='cardholderName')]
    code: Optional[str]
    exp_month: Annotated[Optional[str], Field(alias='expMonth')]
    exp_year: Annotated[Optional[str], Field(alias='expYear')]
    number: Optional[str]


class Identity(BaseModel):
    address1: Optional[str]
    address2: Optional[str]
    address3: Optional[str]
    city: Optional[str]
    company: Optional[str]
    country: Optional[str]
    email: Optional[str]
    first_name: Annotated[Optional[str], Field(alias='firstName')]
    last_name: Annotated[Optional[str], Field(alias='lastName')]
    license_number: Annotated[Optional[str], Field(alias='licenseNumber')]
    middle_name: Annotated[Optional[str], Field(alias='middleName')]
    passport_number: Annotated[Optional[str], Field(alias='passportNumber')]
    phone: Optional[str]
    postal_code: Annotated[Optional[str], Field(alias='postalCode')]
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
    collection_ids: Annotated[Optional[List[UUID]], Field(alias='collectionIds')]
    favorite: Optional[bool]
    fields: Optional[List[FieldModel]]
    folder_id: Annotated[Optional[UUID], Field(alias='folderId')]
    identity: Optional[Identity]
    login: Optional[Login]
    name: Optional[str]
    notes: Optional[str]
    organization_id: Annotated[Optional[UUID], Field(alias='organizationId')]
    reprompt: Optional[Reprompt]
    secure_note: Annotated[Optional[SecureNote], Field(alias='secureNote')]
    type: Optional[Type1Model]
