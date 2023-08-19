from pydantic import Field

from obidog.models.base import CppElement
from obidog.models.classes import ClassModel
from obidog.models.enums import EnumModel
from obidog.models.flags import ObidogFlagsModel
from obidog.models.functions import FunctionUniformModel
from obidog.models.globals import GlobalModel
from obidog.models.typedefs import TypedefModel
from obidog.models.urls import URLs


class NamespaceModel(CppElement):
    name: str = ""
    path: str = ""
    namespace: str = ""
    description: str = ""
    classes: dict[str, ClassModel] = Field(default_factory=dict)
    functions: dict[str, FunctionUniformModel] = Field(default_factory=dict)
    enums: dict[str, EnumModel] = Field(default_factory=dict)
    globals: dict[str, GlobalModel] = Field(default_factory=dict)
    namespaces: dict[str, "NamespaceModel"] = Field(default_factory=dict)
    typedefs: dict[str, TypedefModel] = Field(default_factory=dict)
    flags: ObidogFlagsModel = Field(default_factory=ObidogFlagsModel)
    _type: str = "namespace"
    urls: URLs = Field(default_factory=URLs)
