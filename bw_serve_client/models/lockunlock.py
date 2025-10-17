# Bitwarden Vault Management API Models
# Generated from OpenAPI specification
# DO NOT EDIT MANUALLY

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class Data(BaseModel):
  message: Optional[str] = None
  noColor: Optional[bool] = None
  object: Optional[str] = None
  title: Optional[str] = None


class Success(BaseModel):
  data: Optional[Data] = None
  success: Optional[bool] = None
