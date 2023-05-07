from pydantic import Field

from obidog.models.base import BaseModel
from obidog.models.location import Location


class Export(BaseModel):
    pass


class LuaExport(Export):
    name: str
    location: Location = Field(default_factory=Location)
