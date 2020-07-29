from typing import List

from obidog.models.base import BaseModel
from obidog.models.flags import ObidogFlagsModel
from obidog.models.functions import FunctionBaseModel


class AttributeModel(BaseModel):
    def __init__(self, name: str, type: str, description: str = ""):
        self.name = name
        self.type = type
        self.description = description

class ClassBaseModel(BaseModel):
    def __init__(self, name: str):
        self.name = name

class ClassModel(ClassBaseModel):
    def __init__(
        self,
        name: str,
        abstract: bool = False,
        bases: List[ClassModel] = None,
        attributes: List[AttributeModel] = None,
        methods: List[FunctionBaseModel] = None,
        flags: ObidogFlagsModel = ObidogFlagsModel(),
        description: str = "",
        location: str = "",
    ):
        super().__init__(name)
        self.abstract = abstract
        self.bases = bases if bases is not None else []
        self.attributes = attributes if attributes is not None else []
        self.methods = methods if methods is not None else []
        self.flags = flags
        self.description = description
        self.location = location