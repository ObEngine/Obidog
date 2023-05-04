from dataclasses import dataclass, field
from typing import List

from obidog.models.base import BaseModel
from obidog.models.bindings import Export
from obidog.models.flags import ObidogFlagsModel
from obidog.models.location import Location
from obidog.models.urls import URLs


@dataclass
class EnumValueModel(BaseModel):
    name: str
    description: str
    export: Export = field(default_factory=Export)
    _type: str = "enum_value"


@dataclass
class EnumModel(BaseModel):
    name: str
    values: List[EnumValueModel]
    flags: ObidogFlagsModel = field(default_factory=ObidogFlagsModel)
    namespace: str = ""
    description: str = ""
    location: Location = field(default_factory=Location)
    export: Export = field(default_factory=Export)
    _type: str = "enum"
    urls: URLs = field(default_factory=URLs)
