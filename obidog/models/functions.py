from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any

from obidog.models.base import BaseModel
from obidog.models.bindings import Export
from obidog.models.flags import ObidogFlagsModel
from obidog.models.location import Location
from obidog.models.qualifiers import QualifiersModel
from obidog.models.urls import URLs


@dataclass
class ParameterModel(BaseModel):
    name: str
    type: str
    description: str = ""
    default: Any = None
    export: Export = Export()
    ref: Any = None
    _type: str = "parameter"


@dataclass
class FunctionBaseModel(BaseModel):
    name: str


class FunctionVisibility(Enum):
    Private = "private"
    Protected = "protected"
    Public = "public"


@dataclass
class PlaceholderFunctionModel(FunctionBaseModel):
    visibility: FunctionVisibility = FunctionVisibility.Public


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
    location: Location = field(default_factory=lambda: Location())
    export: Export = Export()
    deleted: bool = False
    abstract: bool = False
    visibility: FunctionVisibility = FunctionVisibility.Public
    _type: str = "function"
    urls: URLs = field(default_factory=lambda: URLs())


@dataclass
class FunctionOverloadModel(FunctionBaseModel):
    overloads: List[FunctionModel]
    flags: ObidogFlagsModel = ObidogFlagsModel()
    force_cast: bool = False
    export: Export = Export()
    _type: str = "overload"


@dataclass
class FunctionPatchModel(FunctionBaseModel):
    definition: str
    parameters: List[ParameterModel]
    return_type: str
    replacement: str
    location: Location = field(default_factory=lambda: Location())
    export: Export = Export()
