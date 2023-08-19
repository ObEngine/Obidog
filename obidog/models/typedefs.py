from pydantic import Field

from obidog.models.base import CppElement
from obidog.models.bindings import Export
from obidog.models.flags import ObidogFlagsModel
from obidog.models.location import Location
from obidog.models.urls import URLs


class TypedefModel(CppElement):
    name: str
    namespace: str
    definition: str
    type: str
    flags: ObidogFlagsModel = Field(default_factory=ObidogFlagsModel)
    description: str = ""
    location: Location = Field(default_factory=Location)
    export: Export = Field(default_factory=Export)
    urls: URLs = Field(default_factory=URLs)
    _type: str = "typedef"
