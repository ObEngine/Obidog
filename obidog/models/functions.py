from dataclasses import dataclass
from typing import List, Dict, Any

from obidog.models.base import BaseModel
from obidog.models.bindings import Export
from obidog.models.flags import ObidogFlagsModel
from obidog.models.qualifiers import QualifiersModel
from obidog.models.urls import URLs


@dataclass
class ParameterModel(BaseModel):
    name: str
    type: str
    description: str = ""
    default: Any = None
    export: Export = Export()


@dataclass
class FunctionBaseModel(BaseModel):
    name: str


@dataclass
class PlaceholderFunctionModel(FunctionBaseModel):
    pass


@dataclass
class FunctionModel(FunctionBaseModel):
    namespace: str
    definition: str
    parameters: List[ParameterModel]
    return_type: str
    template: bool = False
    qualifiers: QualifiersModel = QualifiersModel()
    flags: ObidogFlagsModel = ObidogFlagsModel()
    force_cast: bool = False
    description: str = ""
    location: str = ""
    export: Export = Export()
    type: str = "function"
    urls: URLs = URLs()


@dataclass
class FunctionOverloadModel(FunctionBaseModel):
    overloads: List[FunctionModel]
    flags: ObidogFlagsModel = ObidogFlagsModel()
    force_cast: bool = False
    export: Export = Export()
    type: str = "overload"


@dataclass
class FunctionPatchModel(FunctionBaseModel):
    definition: str
    parameters: List[ParameterModel]
    return_type: str
    replacement: str
    location: str = ""
    export: Export = Export()
