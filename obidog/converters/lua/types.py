from dataclasses import dataclass
from typing import Union

from obidog.databases import CppDatabase
from obidog.models.functions import FunctionModel, FunctionOverloadModel


BASIC_TYPE_MATCH = {
    "void": "nil",
    "bool": "boolean",
    "float": "number",
    "double": "number",
    "int": "number[integer]",
    "unsigned": "number[positive integer]",
    "unsigned int": "number[position integer]",
    "string": "string",
    "std::string": "string",
    "vector": "table",
    "std::vector": "table",
    "pair": "table",
    "std::pair": "table",
    "map": "table",
    "std::map": "table",
    "std::size_t": "number[integer]",
    "std::string_view": "string",
    "std::shared_ptr": "shared pointer",
    "std::weak_ptr": "weak pointer",
    "std::optional": "optional",
    "std::tuple": "table",
    "std::function": "function",
}
LUA_TYPE_MATCH = {"sol::table": "table", "sol::function": "function"}
OTHER_TYPE_MATCH = {"Time::TimeUnit": "number"}
ALL_TYPES_MATCH = {
    **BASIC_TYPE_MATCH,
    **LUA_TYPE_MATCH,
    **OTHER_TYPE_MATCH,
}


def fetch_symbol(cpp_db: CppDatabase, symbol: str):
    symbols = {**cpp_db.classes, **cpp_db.enums, **cpp_db.typedefs}
    return symbols[symbol]


@dataclass
class LuaType:
    prefix: str
    type: str
    suffix: str

    def __str__(self):
        return f"{self.prefix} {self.type} {self.suffix}".strip(" ")


def cpp_type_to_lua_type(cpp_db, cpp_type, lookup_cpp=False):
    if isinstance(cpp_type, LuaType):
        cpp_type = str(cpp_type)
    if "," in cpp_type and not ("<" in cpp_type and ">" in cpp_type):
        return ",".join(
            [
                str(cpp_type_to_lua_type(cpp_db, sub_type, True))
                for sub_type in cpp_type.split(",")
            ]
        )
    cpp_type_backup = cpp_type
    type_prefix = []
    type_suffix = []
    lua_type = ""
    if cpp_type.startswith("const"):
        type_prefix.append("constant")
        cpp_type = cpp_type.removeprefix("const")
    if cpp_type.endswith("&"):
        type_prefix.append("reference to")
        cpp_type = cpp_type.rstrip("&")
    if cpp_type.endswith("*"):
        type_prefix.append("pointer to")
        cpp_type = cpp_type.rstrip("*")
    cpp_type = cpp_type.strip(" ")
    if "<" in cpp_type and ">" in cpp_type:
        cpp_type, *templated_type = cpp_type.split("<")  # LATER: Add templated types
        templated_type[-1] = templated_type[-1][:-1]  # Remove last '>'
        templated_type = "<".join(templated_type)
        type_suffix.append(f"of {cpp_type_to_lua_type(cpp_db, templated_type)}")
    if cpp_type in ALL_TYPES_MATCH:
        lua_type = ALL_TYPES_MATCH[cpp_type]
    else:
        lua_type = ".".join(cpp_type.split("::"))
        """if lookup_cpp:
            lua_type = find_lua_type_from_cpp_type(lua_db, cpp_type)
            if lua_type:
                lua_type = lua_type["lua_name"]
            else:
                return None
        else:
            return FutureLuaReferenceTag(cpp_type_backup)"""
    return LuaType(" ".join(type_prefix), lua_type, " ".join(type_suffix))
    # return f"{lua_type} {' '.join(type_suffix)}".strip(" ")
    # return f"{' '.join(type_prefix)} {lua_type} {' '.join(type_suffix)}".strip(" ")


def convert_function_types(
    cpp_db: CppDatabase, function: Union[FunctionModel, FunctionOverloadModel]
):
    if isinstance(function, FunctionOverloadModel):
        for overload in function.overloads:
            convert_function_types(cpp_db, overload)
    else:
        function.return_type = cpp_type_to_lua_type(cpp_db, function.return_type, True)
        for parameter in function.parameters:
            parameter.type = cpp_type_to_lua_type(cpp_db, parameter.type, True)


def convert_all_types(cpp_db: CppDatabase):
    for class_value in cpp_db.classes.values():
        for method in class_value.methods.values():
            convert_function_types(cpp_db, method)
        for attribute in class_value.attributes.values():
            attribute.type = cpp_type_to_lua_type(cpp_db, attribute.type, True)
    for function in cpp_db.functions.values():
        convert_function_types(cpp_db, function)
    for glob in cpp_db.globals.values():
        glob.type = cpp_type_to_lua_type(cpp_db, glob.type, True)
    for typedef in cpp_db.typedefs.values():
        typedef.type = cpp_type_to_lua_type(cpp_db, typedef.type, True)
