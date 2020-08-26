from dataclasses import dataclass

from obidog.models.base import BaseModel


@dataclass
class URLs(BaseModel):
    documentation: str = ""
    doxygen: str = ""
    source: str = ""
    bindings: str = ""
    example: str = ""
