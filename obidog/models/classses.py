from typing import List

from obidog.models.base import BaseModel
from obidog.models.flags import ObidogFlagsModel
from obidog.models.functions import FunctionBaseModel
from obidog.models.qualifiers import QualifiersModel


class AttributeModel(BaseModel):
    def __init__(
        self,
        name: str,
        type: str,
        qualifiers: QualifiersModel = QualifiersModel(),
        description: str = "",
        flags: ObidogFlagsModel = ObidogFlagsModel()
    ):
        self.name = name
        self.type = type
        self.qualifiers = qualifiers
        self.description = description


class ClassBaseModel(BaseModel):
    def __init__(self, name: str):
        self.name = name


class PlaceholderClassModel(ClassBaseModel):
    def __init__(self, name: str):
        super().__init__(name)


class ClassModel(ClassBaseModel):
    def __init__(
        self,
        name: str,
        abstract: bool = False,
        bases: List[ClassBaseModel] = None,
        attributes: List[AttributeModel] = None,
        constructors: List[FunctionBaseModel] = None,
        destructor: FunctionBaseModel = None,
        methods: List[FunctionBaseModel] = None,
        flags: ObidogFlagsModel = ObidogFlagsModel(),
        description: str = "",
        location: str = "",
    ):
        super().__init__(name)
        self.abstract = abstract
        self.bases = bases if bases is not None else []
        self.attributes = attributes if attributes is not None else []
        self.constructors = constructors if constructors is not None else []
        self.destructor = destructor
        self.methods = methods if methods is not None else []
        self.flags = flags
        self.description = description
        self.location = location
