from dataclasses import dataclass, field
from typing import List, Dict, Union

from obidog.models.base import BaseModel
from obidog.models.classes import ClassModel
from obidog.models.enums import EnumModel
from obidog.models.functions import FunctionModel, FunctionOverloadModel
from obidog.models.globals import GlobalModel
from obidog.models.typedefs import TypedefModel


@dataclass
class Namespace(BaseModel):
    name: str = ""
    path: str = ""
    description: str = ""
    classes: Dict[str, ClassModel] = field(default_factory=lambda: {})
    functions: Dict[str, Union[FunctionModel, FunctionOverloadModel]] = field(
        default_factory=lambda: {}
    )
    enums: Dict[str, EnumModel] = field(default_factory=lambda: {})
    globals: Dict[str, GlobalModel] = field(default_factory=lambda: {})
    namespaces: Dict[str, "Namespace"] = field(default_factory=lambda: {})
    typedefs: Dict[str, TypedefModel] = field(default_factory=lambda: {})
    type: str = "namespace"
