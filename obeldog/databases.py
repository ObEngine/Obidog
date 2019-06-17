class CppDatabase:
    def __init__(self):
        self.classes = {}
        self.typedefs = {}
        self.functions = {}
        self.globals = {}

class LuaDatabase:
    def __init__(self):
        self.classes = {}
        self.functions = {}
        self.variables = {}