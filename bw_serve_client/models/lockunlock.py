# Bitwarden Vault Management API Models
# Generated from OpenAPI specification
# DO NOT EDIT MANUALLY

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class Data(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  message: str | None
  no_color: Annotated[bool | None, Field(alias='noColor')]
  object: str | None
  title: str | None


class Success(BaseModel):
  model_config = ConfigDict(
    extra='forbid',
    populate_by_name=True,
  )
  data: Data | None
  success: bool | None
