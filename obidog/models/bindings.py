from dataclasses import dataclass
from typing import List, Dict

from obidog.models.base import BaseModel


@dataclass
class Export(BaseModel):
    pass


@dataclass
class LuaExport(Export):
    name: str
