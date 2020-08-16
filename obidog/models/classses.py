from dataclasses import dataclass
from typing import List, Dict

from obidog.models.base import BaseModel
from obidog.models.flags import ObidogFlagsModel
from obidog.models.functions import FunctionModel
from obidog.models.qualifiers import QualifiersModel


@dataclass
class AttributeModel(BaseModel):
    name: str
    type: str
    qualifiers: QualifiersModel = QualifiersModel()
    description: str = ""
    flags: ObidogFlagsModel = ObidogFlagsModel()


@dataclass
class ClassBaseModel(BaseModel):
    name: str


@dataclass
class PlaceholderClassModel(ClassBaseModel):
    pass


@dataclass
class ClassModel(ClassBaseModel):
    abstract: bool = False
    bases: List[str] = None
    attributes: Dict[str, AttributeModel] = None
    constructors: List[FunctionModel] = None
    destructor: FunctionModel = None
    methods: Dict[str, FunctionModel] = None
    flags: ObidogFlagsModel = ObidogFlagsModel()
    description: str = ""
    location: str = ""
