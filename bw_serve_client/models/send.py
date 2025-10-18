# Bitwarden Vault Management API Models
# Generated from OpenAPI specification
# DO NOT EDIT MANUALLY


from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import AwareDatetime
from pydantic import BaseModel


class Type(Enum):
    integer_0 = 0
    integer_1 = 1


class Text(BaseModel):
    hidden: Optional[bool]
    text: Optional[str]


class Template(BaseModel):
    deletionDate: Optional[AwareDatetime]
    disabled: Optional[bool]
    expirationDate: Optional[AwareDatetime]
    file: Optional[str]
    hideEmail: Optional[bool]
    maxAccessCount: Optional[int]
    name: Optional[str]
    notes: Optional[str]
    password: Optional[str]
    text: Optional[Text]
    type: Optional[Type]
