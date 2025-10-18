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
    hidden: Optional[bool] = None
    text: Optional[str] = None


class Template(BaseModel):
    deletionDate: Optional[AwareDatetime] = None
    disabled: Optional[bool] = None
    expirationDate: Optional[AwareDatetime] = None
    file: Optional[str] = None
    hideEmail: Optional[bool] = None
    maxAccessCount: Optional[int] = None
    name: Optional[str] = None
    notes: Optional[str] = None
    password: Optional[str] = None
    text: Optional[Text] = None
    type: Optional[Type] = None
