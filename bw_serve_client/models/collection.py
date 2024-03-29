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

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, StrictStr, conlist
from bw_serve_client.models.group import Group


class Collection(BaseModel):
    """
    Collection
    """
    external_id: Optional[StrictStr] = Field(None, alias="externalId")
    groups: Optional[conlist(Group)] = None
    name: Optional[StrictStr] = None
    organization_id: Optional[StrictStr] = Field(None, alias="organizationId")
    additional_properties: Dict[str, Any] = {}
    __properties = ["externalId", "groups", "name", "organizationId"]

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
    def from_json(cls, json_str: str) -> Collection:
        """Create an instance of Collection from a JSON string"""
        return cls.from_dict(json.loads(json_str))

    def to_dict(self):
        """Returns the dictionary representation of the model using alias"""
        _dict = self.dict(by_alias=True,
                          exclude={"additional_properties"},
                          exclude_none=True)
        # override the default output from pydantic by calling `to_dict()` of each item in groups (list)
        _items = []
        if self.groups:
            for _item in self.groups:
                if _item:
                    _items.append(_item.to_dict())
            _dict['groups'] = _items
        # puts key-value pairs in additional_properties in the top level
        if self.additional_properties is not None:
            for _key, _value in self.additional_properties.items():
                _dict[_key] = _value

        return _dict

    @classmethod
    def from_dict(cls, obj: dict) -> Collection:
        """Create an instance of Collection from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return Collection.parse_obj(obj)

        _obj = Collection.parse_obj({
            "external_id":
            obj.get("externalId"),
            "groups": [Group.from_dict(_item) for _item in obj.get("groups")]
            if obj.get("groups") is not None else None,
            "name":
            obj.get("name"),
            "organization_id":
            obj.get("organizationId")
        })
        # store additional fields in additional_properties
        for _key in obj.keys():
            if _key not in cls.__properties:
                _obj.additional_properties[_key] = obj.get(_key)

        return _obj
