from pydantic import Field
from typing import Dict, Union

from obidog.models.base import CppElement
from obidog.models.classes import ClassModel
from obidog.models.enums import EnumModel
from obidog.models.functions import (
    FunctionUniformModel,
)
from obidog.models.globals import GlobalModel
from obidog.models.typedefs import TypedefModel
from obidog.models.flags import ObidogFlagsModel
from obidog.models.urls import URLs


class NamespaceModel(CppElement):
    name: str = ""
    path: str = ""
    namespace: str = ""
    description: str = ""
    classes: Dict[str, ClassModel] = Field(default_factory=dict)
    functions: Dict[str, FunctionUniformModel] = Field(default_factory=dict)
    enums: Dict[str, EnumModel] = Field(default_factory=dict)
    globals: Dict[str, GlobalModel] = Field(default_factory=dict)
    namespaces: Dict[str, "NamespaceModel"] = Field(default_factory=dict)
    typedefs: Dict[str, TypedefModel] = Field(default_factory=dict)
    flags: ObidogFlagsModel = Field(default_factory=ObidogFlagsModel)
    _type: str = "namespace"
    urls: URLs = Field(default_factory=URLs)
