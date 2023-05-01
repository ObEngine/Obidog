from typing import Dict

from obidog.models.classes import ClassModel
from obidog.models.enums import EnumModel
from obidog.models.functions import FunctionBaseModel
from obidog.models.globals import GlobalModel
from obidog.models.namespace import NamespaceModel
from obidog.models.typedefs import TypedefModel


class CppDatabase:
    def __init__(self):
        self.classes: Dict[str, ClassModel] = {}
        self.typedefs: Dict[str, TypedefModel] = {}
        self.functions: Dict[str, FunctionBaseModel] = {}
        self.globals: Dict[str, GlobalModel] = {}
        self.enums: Dict[str, EnumModel] = {}
        self.namespaces: Dict[str, NamespaceModel] = {}


class LuaDatabase:
    def __init__(self):
        self.classes = {}
        self.functions = {}
        self.variables = {}
