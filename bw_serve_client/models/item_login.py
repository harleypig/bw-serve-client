# coding: utf-8

"""
    Vault Management API

    This schema documents the endpoints available to the Vault Management API, accessible from the Bitwarden CLI using the `bw serve` command ([learn more](https://bitwarden.com/help/cli/)). If you're looking for the **Organization Management** API, refer instead to [this document](https://bitwarden.com/help/api/).

    The version of the OpenAPI document: latest
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501

from __future__ import annotations
import pprint
import re  # noqa: F401
import json

from typing import Any, Dict, Optional
from pydantic import BaseModel, StrictStr
from bw_serve_client.models.uris import Uris


class ItemLogin(BaseModel):
    """
    ItemLogin
    """
    password: Optional[StrictStr] = None
    totp: Optional[StrictStr] = None
    uris: Optional[Uris] = None
    username: Optional[StrictStr] = None
    additional_properties: Dict[str, Any] = {}
    __properties = ["password", "totp", "uris", "username"]

    class Config:
        """Pydantic configuration"""
        allow_population_by_field_name = True
        validate_assignment = True

    def to_str(self) -> str:
        """Returns the string representation of the model using alias"""
        return pprint.pformat(self.dict(by_alias=True))

    def to_json(self) -> str:
        """Returns the JSON representation of the model using alias"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> ItemLogin:
        """Create an instance of ItemLogin from a JSON string"""
        return cls.from_dict(json.loads(json_str))

    def to_dict(self):
        """Returns the dictionary representation of the model using alias"""
        _dict = self.dict(by_alias=True,
                          exclude={"additional_properties"},
                          exclude_none=True)
        # override the default output from pydantic by calling `to_dict()` of uris
        if self.uris:
            _dict['uris'] = self.uris.to_dict()
        # puts key-value pairs in additional_properties in the top level
        if self.additional_properties is not None:
            for _key, _value in self.additional_properties.items():
                _dict[_key] = _value

        return _dict

    @classmethod
    def from_dict(cls, obj: dict) -> ItemLogin:
        """Create an instance of ItemLogin from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return ItemLogin.parse_obj(obj)

        _obj = ItemLogin.parse_obj({
            "password":
            obj.get("password"),
            "totp":
            obj.get("totp"),
            "uris":
            Uris.from_dict(obj.get("uris"))
            if obj.get("uris") is not None else None,
            "username":
            obj.get("username")
        })
        # store additional fields in additional_properties
        for _key in obj.keys():
            if _key not in cls.__properties:
                _obj.additional_properties[_key] = obj.get(_key)

        return _obj
