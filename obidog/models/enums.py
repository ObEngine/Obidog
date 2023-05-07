from pydantic import Field
from typing import List

from obidog.models.base import CppElement
from obidog.models.bindings import Export
from obidog.models.flags import ObidogFlagsModel
from obidog.models.location import Location
from obidog.models.urls import URLs


class EnumValueModel(CppElement):
    name: str
    description: str = ""
    export: Export = Field(default_factory=Export)
    _type: str = "enum_value"


class EnumModel(CppElement):
    name: str
    values: List[EnumValueModel]
    flags: ObidogFlagsModel = Field(default_factory=ObidogFlagsModel)
    namespace: str = ""
    description: str = ""
    location: Location = Field(default_factory=Location)
    export: Export = Field(default_factory=Export)
    _type: str = "enum"
    urls: URLs = Field(default_factory=URLs)
