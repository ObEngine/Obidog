from dataclasses import dataclass

from obidog.models.base import BaseModel


@dataclass
class GlobalModel(BaseModel):
    name: str
    definition: str
    type: str
    initializer: str = ""
    location: str = ""
    description: str = ""
