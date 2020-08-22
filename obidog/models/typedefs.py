from dataclasses import dataclass

from obidog.models.base import BaseModel
from obidog.models.flags import ObidogFlagsModel


@dataclass
class TypedefModel(BaseModel):
    name: str
    definition: str
    type: str
    flags: ObidogFlagsModel = ObidogFlagsModel()
    description: str = ""
    location: str = ""
