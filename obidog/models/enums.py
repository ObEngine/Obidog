from typing import List

from obidog.models.base import BaseModel
from obidog.models.flags import ObidogFlagsModel


class EnumValueModel(BaseModel):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description


class EnumModel(BaseModel):
    def __init__(
        self,
        name: str,
        values: List[EnumValueModel],
        flags: ObidogFlagsModel = ObidogFlagsModel(),
        description: str = "",
        location: str = "",
    ):
        self.name = name
        self.values = values
        self.flags = flags
        self.description = description
        self.location = location
