STATE_VIEW = "sol::state_view"
INCLUDE_FILE = "sol/sol.hpp"
CLASS_BODY = """
sol::table {namespace} = state.get<sol::table>("{namespace}");
sol::usertype<{cpp_class}> bind{lua_short_name} = {namespace}.new_usertype<{cpp_class}>(
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
METHOD = "{address}"
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