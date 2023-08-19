from obidog.models.classes import ClassModel
from obidog.models.enums import EnumModel
from obidog.models.functions import FunctionBaseModel
from obidog.models.globals import GlobalModel
from obidog.models.namespace import NamespaceModel
from obidog.models.typedefs import TypedefModel


class CppDatabase:
    def __init__(self):
        self.classes: dict[str, ClassModel] = {}
        self.typedefs: dict[str, TypedefModel] = {}
        self.functions: dict[str, FunctionBaseModel] = {}
        self.globals: dict[str, GlobalModel] = {}
        self.enums: dict[str, EnumModel] = {}
        self.namespaces: dict[str, NamespaceModel] = {}


class LuaDatabase:
    def __init__(self):
        self.classes = {}
        self.functions = {}
        self.variables = {}
