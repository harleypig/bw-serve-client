# Bitwarden Vault Management API Models
# Generated from OpenAPI specification
# DO NOT EDIT MANUALLY

from __future__ import annotations

from typing import Annotated, Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class Data(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  message: Optional[str]
  no_color: Annotated[Optional[bool], Field(alias='noColor')]
  object: Optional[str]
  title: Optional[str]


class Success(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  data: Optional[Data]
  success: Optional[bool]
