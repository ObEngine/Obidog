from dataclasses import dataclass, field
from typing import List, Any, Optional

from obidog.models.base import BaseModel, ItemVisibility
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
    namespace: str


@dataclass
class PlaceholderFunctionModel(FunctionBaseModel):
    visibility: ItemVisibility = ItemVisibility.Public


@dataclass
class FunctionModel(FunctionBaseModel):
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
    visibility: ItemVisibility = ItemVisibility.Public
    # FQN of proxy function
    replacement: Optional[str] = None
    from_class: Optional[str] = None
    constructor: bool = False
    _type: str = "function"
    urls: URLs = field(default_factory=lambda: URLs())


@dataclass
class FunctionOverloadModel(FunctionBaseModel):
    overloads: List[FunctionModel]
    flags: ObidogFlagsModel = ObidogFlagsModel()
    force_cast: bool = False
    from_class: Optional[str] = None
    export: Export = Export()
    _type: str = "overload"

    def to_function_model(self) -> FunctionModel:
        return FunctionModel(
            name=self.name,
            namespace=self.namespace,
            definition=None,
            parameters=[],
            from_class=self.from_class,
            return_type=None,
        )


@dataclass
class FunctionPatchModel(FunctionBaseModel):
    definition: str
    parameters: List[ParameterModel]
    return_type: str
    replacement: str
    location: Location = field(default_factory=lambda: Location())
    export: Export = Export()
