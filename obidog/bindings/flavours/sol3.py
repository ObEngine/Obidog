STATE_VIEW = "sol::state_view"
INCLUDE_FILE = "sol/sol.hpp"
CALL_CONSTRUCTOR = "sol::call_constructor"
CLASS_BODY = """
sol::usertype<{cpp_class}> bind_{lua_formatted_name} = {namespace}_namespace.new_usertype<{cpp_class}>(
"{lua_short_name}"{class_definition});
{body}
{helpers}
{hooks}
""".strip(
    "\n"
)
STATIC_ATTRIB = "sol::var(&{name})"
PROPERTY = "sol::property({address})"
PROPERTY_REF = "sol::property([]({class_name}* self) -> {property_type}* {{ return &self->{attribute_name}; }})"
PROPERTY_READONLY = "sol::readonly({address})"
DEFAULT_CONSTRUCTOR = "sol::default_constructor"
DESTRUCTOR = "sol::destructor({destructor})"
CONSTRUCTORS = "sol::constructors<{constructors}>()"
BASE_CLASSES = "sol::base_classes, sol::bases<{bases}>()"
SCRIPT_FILE = 'state.script_file("{source}"_fs);'
METHOD = "{address}"
# LATER: Add missing elements, even the ones not in sol::meta_function
OPERATOR_TRANSLATION_TABLE = {
    "operator+": "sol::meta_function::addition",
    "operator-": {
        "sol::meta_function::subtraction": lambda f: (
            f.from_class and len(f.parameters) == 1
        )
        or (len(f.parameters) > 1),
        "sol::meta_function::unary_minus": lambda f: (
            f.from_class and len(f.parameters) == 0
        ),
    },
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
    "operator[]": "sol::meta_function::index",
    "operator%": "sol::meta_function::modulus",
    "operator=": None,
}
FETCH_TABLE = """
sol::table {store_in} = state{namespace_path}.get<sol::table>();
""".strip(
    "\n"
)
ENUM_BODY = """
{namespace}_namespace.new_enum<{enum_type}>("{enum_name}", {enum_fields});
""".strip(
    "\n"
)
FUNCTION_BODY = """
{namespace}_namespace.set_function("{function_name}", {function_ptr});
""".strip(
    "\n"
)
FUNCTION_OVERLOAD = "sol::overload({overloads})"
GLOBAL_BODY = """
{namespace}_namespace["{global_name}"] = {global_ptr};
""".strip(
    "\n"
)
SHORTHAND = """
state{shorthand_path} = state{namespace_path}
"""
