from obidog.models.base import BaseModel
from obidog.models.flags import ObidogFlagsModel


class TypedefModel(BaseModel):
    def __init__(
        self,
        name: str,
        definition: str,
        type: str,
        flags: ObidogFlagsModel = ObidogFlagsModel(),
        description: str = "",
        location: str = "",
    ):
        self.name = name
        self.definition = definition
        self.type = type
        self.flags = flags
        self.description = description
        self.location = location
