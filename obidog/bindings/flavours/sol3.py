STATE_VIEW = "sol::state_view"
INCLUDE_FILE = "sol/sol.hpp"
CLASS_BODY = """
sol::usertype<{cpp_class}> bind{lua_short_name} = {namespace}Namespace.new_usertype<{cpp_class}>(
"{lua_short_name}", sol::call_constructor,
{class_definition}
);
{body}
{helpers}
""".strip("\n")
PROPERTY = "sol::readonly({address})"
DEFAULT_CONSTRUCTOR = "sol::default_constructor"
DESTRUCTOR = "sol::destructor({destructor})"
CONSTRUCTORS = "sol::constructors<{constructors}>()"
BASE_CLASSES = "sol::base_classes, sol::bases<{bases}>()"
METHOD = "{address}"
# LATER: Add missing elements, even the ones not in sol::meta_function
TRANSLATION_TABLE = {
    "operator+": "sol::meta_function::addition",
    "operator-": "sol::meta_function::subtraction",
    "operator*": "sol::meta_function::multiplication",
    "operator/": "sol::meta_function::division",
    "operator==": "sol::meta_function::equal_to",
    "operator()": "sol::meta_function::call",
    "operator<": "sol::meta_function::less_than",
    "operator<=": "sol::meta_function::less_than_or_equal_to",
    "operator!=": None,
    "operator+=": None,
    "operator-=": None,
    "operator*=": None,
    "operator/=": None,
}
FETCH_TABLE = """
sol::table {namespace}Namespace = state{namespace_path}.get<sol::table>();
""".strip("\n")
ENUM_BODY = """
{namespace}Namespace.new_enum<{enum_type}>("{enum_name}", {enum_fields});
""".strip("\n")
FUNCTION_BODY = """
{namespace}Namespace.set_function("{function_name}", {function_ptr});
""".strip("\n")
FUNCTION_OVERLOAD = "sol::overload({overloads});"
GLOBAL_BODY = """
{namespace}Namespace["{global_name}"] = {global_ptr};
""".strip("\n")
SHORTHAND = """
state{shorthand_path} = state{namespace_path}
"""