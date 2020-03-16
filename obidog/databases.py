class CppDatabase:
    def __init__(self):
        self.classes = {}
        self.typedefs = {}
        self.functions = {}
        self.globals = {}
        self.enums = {}
        self.namespaces = {}

class LuaDatabase:
    def __init__(self):
        self.classes = {}
        self.functions = {}
        self.variables = {}