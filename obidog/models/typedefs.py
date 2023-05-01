from dataclasses import dataclass, field

from obidog.models.base import BaseModel
from obidog.models.bindings import Export
from obidog.models.flags import ObidogFlagsModel
from obidog.models.location import Location
from obidog.models.urls import URLs


@dataclass
class TypedefModel(BaseModel):
    name: str
    namespace: str
    definition: str
    type: str
    flags: ObidogFlagsModel = field(default_factory=ObidogFlagsModel)
    description: str = ""
    location: Location = field(default_factory=Location)
    export: Export = field(default_factory=Export)
    urls: URLs = field(default_factory=URLs)
    _type: str = "typedef"
