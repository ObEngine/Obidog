from dataclasses import dataclass, field

from obidog.models.base import BaseModel
from obidog.models.bindings import Export
from obidog.models.flags import ObidogFlagsModel
from obidog.models.location import Location
from obidog.models.urls import URLs


@dataclass
class GlobalModel(BaseModel):
    name: str
    definition: str
    type: str
    namespace: str = ""
    initializer: str = ""
    location: Location = field(default_factory=lambda: Location())
    description: str = ""
    flags: ObidogFlagsModel = ObidogFlagsModel()
    export: Export = Export()
    urls: URLs = field(default_factory=lambda: URLs())
    _type: str = "global"
