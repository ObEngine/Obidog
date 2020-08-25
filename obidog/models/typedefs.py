from dataclasses import dataclass

from obidog.models.base import BaseModel
from obidog.models.bindings import Export
from obidog.models.flags import ObidogFlagsModel
from obidog.models.urls import URLs


@dataclass
class TypedefModel(BaseModel):
    name: str
    definition: str
    type: str
    flags: ObidogFlagsModel = ObidogFlagsModel()
    description: str = ""
    location: str = ""
    namespace: str = ""
    export: Export = Export()
    urls: URLs = URLs()
