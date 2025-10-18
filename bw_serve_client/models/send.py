# Bitwarden Vault Management API Models
# Generated from OpenAPI specification
# DO NOT EDIT MANUALLY

from __future__ import annotations

from enum import Enum
from typing import Annotated, Optional

from pydantic import AwareDatetime
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class Template(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  deletion_date: Annotated[Optional[AwareDatetime], Field(alias='deletionDate')]
  disabled: Optional[bool]
  expiration_date: Annotated[Optional[AwareDatetime], Field(alias='expirationDate')]
  file: Optional[str]
  hide_email: Annotated[Optional[bool], Field(alias='hideEmail')]
  max_access_count: Annotated[Optional[int], Field(alias='maxAccessCount')]
  name: Optional[str]
  notes: Optional[str]
  password: Optional[str]
  text: Optional[Text]
  type: Optional[Type]


class Text(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  hidden: Optional[bool]
  text: Optional[str]


class Type(Enum):
  INTEGER_0 = 0
  INTEGER_1 = 1
