# Bitwarden Vault Management API Models
# Generated from OpenAPI specification
# DO NOT EDIT MANUALLY

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import AwareDatetime
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class Template(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  deletion_date: Annotated[AwareDatetime | None, Field(alias='deletionDate')]
  disabled: bool | None
  expiration_date: Annotated[AwareDatetime | None, Field(alias='expirationDate')]
  file: str | None
  hide_email: Annotated[bool | None, Field(alias='hideEmail')]
  max_access_count: Annotated[int | None, Field(alias='maxAccessCount')]
  name: str | None
  notes: str | None
  password: str | None
  text: Text | None
  type: Type | None


class Text(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  hidden: bool | None
  text: str | None


class Type(Enum):
  INTEGER_0 = 0
  INTEGER_1 = 1
