from dataclasses import dataclass, field

from obidog.models.base import BaseModel
from obidog.models.location import Location


@dataclass
class Export(BaseModel):
    pass


@dataclass
class LuaExport(Export):
    name: str
    location: Location = field(default_factory=lambda: Location())
