from dataclasses import dataclass

from obidog.models.base import BaseModel


@dataclass
class Location(BaseModel):
    file: str = ""
    line: int = -1
    column: int = -1
