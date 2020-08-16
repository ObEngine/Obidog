from dataclasses import dataclass
from typing import List

from obidog.models.base import BaseModel
from obidog.models.flags import ObidogFlagsModel


@dataclass
class EnumValueModel(BaseModel):
    name: str
    description: str


@dataclass
class EnumModel(BaseModel):
    name: str
    values: List[EnumValueModel]
    flags: ObidogFlagsModel = ObidogFlagsModel()
    description: str = ""
    location: str = ""
