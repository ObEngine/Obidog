from typing import Optional
from pydantic import Field

from obidog.models.base import CppElement
from obidog.models.bindings import Export
from obidog.models.flags import ObidogFlagsModel
from obidog.models.location import Location
from obidog.models.urls import URLs


class GlobalModel(CppElement):
    name: str
    definition: str
    type: str
    namespace: str = ""
    initializer: Optional[str]
    location: Location = Field(default_factory=Location)
    description: str = ""
    flags: ObidogFlagsModel = Field(default_factory=ObidogFlagsModel)
    export: Export = Field(default_factory=Export)
    urls: URLs = Field(default_factory=URLs)
    _type: str = "global"
