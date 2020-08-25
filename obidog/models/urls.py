from dataclasses import dataclass

from obidog.models.base import BaseModel


@dataclass
class URLs(BaseModel):
    doxygen: str = ""
    source: str = ""
    bindings: str = ""
    example: str = ""
