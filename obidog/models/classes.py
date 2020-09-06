from dataclasses import dataclass, field
from typing import List, Dict

from obidog.models.base import BaseModel
from obidog.models.bindings import Export
from obidog.models.flags import ObidogFlagsModel
from obidog.models.functions import FunctionModel
from obidog.models.location import Location
from obidog.models.qualifiers import QualifiersModel
from obidog.models.urls import URLs


@dataclass
class AttributeModel(BaseModel):
    name: str
    type: str
    qualifiers: QualifiersModel = QualifiersModel()
    description: str = ""
    flags: ObidogFlagsModel = ObidogFlagsModel()
    export: Export = Export()
    _type: str = "attribute"
    urls: URLs = URLs()


@dataclass
class ClassBaseModel(BaseModel):
    name: str


@dataclass
class PlaceholderClassModel(ClassBaseModel):
    pass


@dataclass
class ClassModel(ClassBaseModel):
    namespace: str = ""
    abstract: bool = False
    bases: List[str] = None
    attributes: Dict[str, AttributeModel] = None
    constructors: List[FunctionModel] = None
    destructor: FunctionModel = None
    methods: Dict[str, FunctionModel] = None
    flags: ObidogFlagsModel = ObidogFlagsModel()
    description: str = ""
    location: Location = field(default_factory=lambda: Location())
    export: Export = Export()
    _type: str = "class"
    urls: URLs = field(default_factory=lambda: URLs())
