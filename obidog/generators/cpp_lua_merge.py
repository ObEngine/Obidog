from obidog.utils.dict_utils import merge_dicts
from obidog.logger import log

class FutureLuaReferenceTag:
    def __init__(self, cpp_type):
        self.cpp_type = cpp_type

def get_all_lua_elements(elements, element_type=["class", "function", "variable"]):
    result = []
    for lua_element in elements.values():
        if isinstance(lua_element, dict):
            if "type" in lua_element and lua_element["type"] in element_type:
                result.append(lua_element)
            result += get_all_lua_elements(lua_element, element_type)
    return result


def find_lua_type_from_cpp_type(lua_db, cpp_type_name):
    all_base_elements = merge_dicts(
        lua_db.functions,
        lua_db.variables,
        lua_db.classes
    )
    elements = get_all_lua_elements(all_base_elements)
    for lua_element in elements:
        if lua_element["reference"] in [cpp_type_name, cpp_type_name.lstrip("obe::")]:
            return lua_element
    log.warning(f"Unknown cpptype : '{cpp_type_name}'")
    return None

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
    "std::map": "table"
}
LUA_TYPE_MATCH = {
    "kaguya::LuaTable": "table",
    "kaguya::LuaFunction": "function"
}
SFML_TYPE_MATCH = {
    "sf::Vector3f": "SFML.Vector3f",
    "sf::Time": "SFML.Time",
    "sf::Color": "obe.Color"
}
OTHER_TYPE_MATCH = {
    "Time::TimeUnit": "number"
}
ALL_TYPES_MATCH = {
    **BASIC_TYPE_MATCH,
    **LUA_TYPE_MATCH,
    **SFML_TYPE_MATCH,
    **OTHER_TYPE_MATCH
}
def cpp_type_to_lua_type(lua_db, cpp_type, lookup_cpp = False):
    cpp_type_backup = cpp_type
    type_prefix = []
    lua_type = ""
    if cpp_type.startswith("const"):
        type_prefix.append("constant")
        cpp_type = cpp_type.lstrip("const")
    if cpp_type.endswith("&"):
        type_prefix.append("reference to")
        cpp_type = cpp_type.rstrip("&")
    if cpp_type.endswith("*"):
        type_prefix.append("pointer to")
        cpp_type = cpp_type.rstrip("*")
    cpp_type = cpp_type.strip(" ")
    if "<" in cpp_type and ">" in cpp_type:
        cpp_type = cpp_type.split("<")[0] # TODO: Add templated types
    if cpp_type in ALL_TYPES_MATCH:
        lua_type = ALL_TYPES_MATCH[cpp_type]
    else:
        if lookup_cpp:
            lua_type = find_lua_type_from_cpp_type(lua_db, cpp_type)
            if lua_type:
                lua_type = lua_type["lua_name"]
            else:
                return None
        else:
            return FutureLuaReferenceTag(cpp_type_backup)
    return f"{' '.join(type_prefix)} {lua_type}".strip(" ")

def mix_cpp_lua_doc(cpp_db, lua_db):
    all_classes = get_all_lua_elements(lua_db.classes["obe"], ["class"])
    for lua_class in all_classes:
        for method in lua_class["methods"].values():
            if method["function_ptr"].endswith("_wrapper()"):
                pass
            elif method["function_ptr"].startswith("static_cast<"):
                pass
            else:
                splitted_cpp_function_ptr = method["function_ptr"].lstrip("&").split("<")[0].split("::")
                cpp_class_name = "::".join(splitted_cpp_function_ptr[:-1])
                if not cpp_class_name.startswith("obe::"):
                    cpp_class_name = "obe::" + cpp_class_name
                cpp_method_name = splitted_cpp_function_ptr[-1]
                cpp_method = cpp_db.classes[cpp_class_name]["methods"][cpp_method_name]
                method["description"] = cpp_method["description"]
                lua_return_type = cpp_type_to_lua_type(lua_db, cpp_method["returnType"])
                if lua_return_type is None:
                    lua_return_type = cpp_method["returnType"]
                    log.warning(f"Unknown Return Type '{lua_return_type}' for {lua_class['name']}::{cpp_method_name}")
                method["return_type"] = lua_return_type
                method["parameters"] = {}
                for cpp_method_parameter_name, cpp_method_parameter in cpp_method["parameters"].items():
                    #lua_method_parameter_type =
                    lua_parameter_type = cpp_type_to_lua_type(lua_db, cpp_method_parameter["type"])
                    if lua_parameter_type is None:
                        lua_parameter_type = cpp_method_parameter["type"]
                        log.warning(f"Unknown Parameter Type '{lua_parameter_type}' for {lua_class['name']}::{cpp_method_name}")
                    method["parameters"][cpp_method_parameter_name] = {
                        "reference": cpp_method_parameter["name"],
                        "type": lua_parameter_type,
                    }
                    if "description" in cpp_method_parameter:
                        method["parameters"][cpp_method_parameter_name]["description"] = cpp_method_parameter["description"]
    return all_classes

def transform_all_cpp_types_to_lua_types(lua_db):
    all_classes = get_all_lua_elements(lua_db.classes["obe"], ["class"])
    for lua_class in all_classes:
        for method in lua_class["methods"].values():
            if "return_type" in method and isinstance(method["return_type"], FutureLuaReferenceTag):
                lua_type = cpp_type_to_lua_type(lua_db, method["return_type"].cpp_type, True)
                if lua_type:
                    method["return_type"] = lua_type
                else:
                    method["return_type"] = method["return_type"].cpp_type
                    log.warning(f"Can't find reference to type '{method['return_type']}' !")