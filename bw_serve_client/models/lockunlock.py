# Bitwarden Vault Management API Models
# Generated from OpenAPI specification
# DO NOT EDIT MANUALLY


from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class Data(BaseModel):
    message: Optional[str]
    noColor: Optional[bool]
    object: Optional[str]
    title: Optional[str]


class Success(BaseModel):
    data: Optional[Data]
    success: Optional[bool]
