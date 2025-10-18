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


class Type(Enum):
  INTEGER_0 = 0
  INTEGER_1 = 1


class Text(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  text: str | None
  hidden: bool | None


class Template(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  name: str | None
  notes: str | None
  type: Type | None
  text: Text | None
  file: str | None
  max_access_count: Annotated[int | None, Field(alias='maxAccessCount')]
  deletion_date: Annotated[AwareDatetime | None, Field(alias='deletionDate')]
  expiration_date: Annotated[AwareDatetime | None, Field(alias='expirationDate')]
  password: str | None
  disabled: bool | None
  hide_email: Annotated[bool | None, Field(alias='hideEmail')]
