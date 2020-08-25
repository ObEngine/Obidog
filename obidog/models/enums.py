from dataclasses import dataclass
from typing import List

from obidog.models.base import BaseModel
from obidog.models.bindings import Export
from obidog.models.flags import ObidogFlagsModel
from obidog.models.urls import URLs


@dataclass
class EnumValueModel(BaseModel):
    name: str
    description: str
    export: Export = Export()
    type: str = "enum_value"


@dataclass
class EnumModel(BaseModel):
    name: str
    values: List[EnumValueModel]
    flags: ObidogFlagsModel = ObidogFlagsModel()
    namespace: str = ""
    description: str = ""
    location: str = ""
    export: Export = Export()
    type: str = "enum"
    urls: URLs = URLs()
