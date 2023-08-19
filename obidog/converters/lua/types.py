import re

from obidog.databases import CppDatabase
from obidog.logger import log
from obidog.models.bindings import LuaType
from obidog.models.functions import FunctionOverloadModel, FunctionUniformModel
from obidog.parsers.type_parser import split_root_types

PRIMITIVE_TYPES = {
    "bool": "boolean",
    "char": "string",
    "double": "number",
    "double float": "number",
    "float": "number",
    "int": "number",
    "int16_t": "number",
    "int32_t": "number",
    "int64_t": "number",
    "int8_t": "number",
    "long": "number",
    "long double": "number",
    "long double float": "number",
    "long int": "number",
    "long long": "number",
    "long long int": "number",
    "signed char": "number",
    "signed int": "number",
    "signed long": "number",
    "signed long int": "number",
    "signed long long": "number",
    "signed long long int": "number",
    "signed short": "number",
    "signed short int": "number",
    "short": "number",
    "short int": "number",
    "size_t": "number",
    "std::function": "function",
    "std::int16_t": "number",
    "std::int32_t": "number",
    "std::int64_t": "number",
    "std::int8_t": "number",
    "std::size_t": "number",
    "std::string": "string",
    "std::string_view": "string",
    "std::tuple": "table",
    "std::uint16_t": "number",
    "std::uint32_t": "number",
    "std::uint64_t": "number",
    "std::uint8_t": "number",
    "string": "string",
    "uint16_t": "number",
    "uint32_t": "number",
    "uint64_t": "number",
    "uint8_t": "number",
    "unsigned": "number",
    "unsigned char": "number",
    "unsigned int": "number",
    "unsigned long": "number",
    "unsigned long int": "number",
    "unsigned long long": "number",
    "unsigned long long int": "number",
    "unsigned short": "number",
    "unsigned short int": "number",
    "void": "nil",
}
STD_TYPES = {
    "map": "table",
    "pair": "table",
    "std::map": "table",
    "std::monostate": "nil",
    "std::optional": "optional",
    "std::pair": "table",
    "std::shared_ptr": "shared_pointer",
    "std::unoredered_map": "table",
    "std::vector": "table",
    "std::weak_ptr": "weak_pointer",
    "vector": "table",
}
LUA_BINDING_TYPES = {
    "sol::table": "table",
    "sol::function": "function",
    "sol::protected_function": "function",
}
OTHER_TYPE_MATCH = {
    "obe::Animation::Easing::Easing::EasingFunction": "function",
    "Transform::UnitVector": "obe.Transform.UnitVector",
    "Color": "obe.Graphics.Color",
    "Graphics::Color": "obe.Graphics.Color",
    "Graphics::Text": "obe.Graphics.Text",
    "Shapes::Circle": "obe.Graphics.Shapes.Circle",
    "Shapes::Rectangle": "obe.Graphics.Shapes.Rectangle",
    "Shapes::Text": "obe.Graphics.Shapes.Text",
    "Shapes::Polygon": "obe.Graphics.Shapes.Polygon",
    "TextHorizontalAlign": "obe.Graphics.Canvas.TextHorizontalAlign",
    "TextVerticalAlign": "obe.Graphics.Canvas.TextVerticalAlign",
    "CoordinateTransformer": "obe.Graphics.CoordinateTransformer",
    "Movable": "obe.Transform.Movable",
    "MountablePathType": "obe.System.MountablePathType",
    "PolygonPoint": "obe.Transform.PolygonPoint",
    "Referential": "obe.Transform.Referential",
    "Units": "obe.Transform.Units",
    "Input::InputAction": "obe.Input.InputAction",
    "Input::InputCondition": "obe.Input.InputCondition",
    "Canvas": "obe.Graphics.Canvas.Canvas",
    "CanvasElementType": "obe.Graphics.Canvas.CanvasElementType",
    "Cursor": "obe.System.Cursor",
    "Input::InputButtonState": "obe.Input.InputButtonState",
    "TimeUnit": "obe.Time.TimeUnit",
    "PolygonalCollider": "obe.Collision.PolygonalCollider",
}
ALL_TYPES_MATCH = {
    **PRIMITIVE_TYPES,
    **STD_TYPES,
    **LUA_BINDING_TYPES,
    **OTHER_TYPE_MATCH,
}


def fetch_symbol(cpp_db: CppDatabase, symbol: str):
    symbols = {**cpp_db.classes, **cpp_db.enums, **cpp_db.typedefs}
    return symbols[symbol]


# TODO: open issue on Doxygen
def horrible_doxygen_parse_error_patch(cpp_type: str) -> str:
    return re.sub(">([a-zA-Z])", r">(\1", cpp_type)


def prepare_and_strip_type(cpp_type: str) -> str:
    cpp_type = cpp_type.strip(" ")
    if cpp_type.startswith("const "):
        cpp_type = cpp_type.removeprefix("const ")
    if cpp_type.startswith("constexpr "):
        cpp_type = cpp_type.removeprefix("constexpr ")
    if cpp_type.startswith("static "):
        cpp_type = cpp_type.removeprefix("static ")
    if cpp_type.endswith("&"):
        cpp_type = cpp_type.rstrip("&")
    if cpp_type.endswith("*"):
        cpp_type = cpp_type.rstrip("*")
    return cpp_type.strip()


class DynamicTupleType:
    def __init__(self, sub_types: list[str]):
        self.sub_types = sub_types

    def __str__(self):
        prefix = "Tuple_"
        capitalized_sub_types = []
        for sub_type in self.sub_types:
            sub_typename = sub_type.type
            segments = re.split(r"\W", sub_typename)
            capitalized_sub_types.append(
                "".join(
                    [
                        segment[0].upper() + segment[1::]
                        for segment in segments
                        if segment.strip()
                    ]
                )
            )

        return prefix + "_".join(capitalized_sub_types)


class DynamicTypesCollection:
    """Used to store types that are dynamically created
    for lua (such as std::tuple and std::pair)
    """

    def __init__(self):
        self.dynamic_types = {}

    def add_tuple_type(self, sub_types: list[str]):
        new_type = DynamicTupleType(sub_types)
        self.dynamic_types[str(new_type)] = new_type
        return str(new_type)


DYNAMIC_TYPES = DynamicTypesCollection()


def cpp_type_to_lua_type(cpp_db, cpp_type):
    if isinstance(cpp_type, LuaType):
        cpp_type = str(cpp_type)
    if "," in cpp_type and not ("<" in cpp_type and ">" in cpp_type):
        return ",".join(
            [
                str(cpp_type_to_lua_type(cpp_db, sub_type))
                for sub_type in cpp_type.split(",")
            ]
        )
    cpp_type_backup = cpp_type
    if cpp_type.strip().startswith("std::function"):
        cpp_type = horrible_doxygen_parse_error_patch(cpp_type)
    lua_type = ""
    cpp_type = prepare_and_strip_type(cpp_type)
    if "<" in cpp_type and ">" in cpp_type:
        cpp_type, *templated_type = cpp_type.split("<")  # LATER: Add templated types
        templated_type[-1] = templated_type[-1].strip().removesuffix(">").strip()
        cpp_type = cpp_type.strip()
        templated_type = "<".join(templated_type).strip()
        sub_types = split_root_types(templated_type)
        if cpp_type == "std::optional":
            lua_type = f"{cpp_type_to_lua_type(cpp_db, templated_type)}?"
        elif cpp_type in ["std::vector", "std::array"]:
            lua_type = f"{cpp_type_to_lua_type(cpp_db, sub_types[0])}[]"
        elif cpp_type in ["std::unordered_map", "std::map"]:
            lua_type = f"table<{cpp_type_to_lua_type(cpp_db, sub_types[0])}, {cpp_type_to_lua_type(cpp_db, sub_types[1])}>"
        elif cpp_type in ["std::pair", "std::tuple"]:
            if all(sub_type == sub_types[0] for sub_type in sub_types):
                lua_type = (
                    f"table<number, {cpp_type_to_lua_type(cpp_db, sub_types[0])}>"
                )
            else:
                tuple_types = [
                    cpp_type_to_lua_type(cpp_db, variant_elem)
                    for variant_elem in sub_types
                ]
                lua_type = DYNAMIC_TYPES.add_tuple_type(tuple_types)
        elif cpp_type == "sol::nested":
            return cpp_type_to_lua_type(cpp_db, sub_types[0])
        elif cpp_type in ["std::shared_ptr", "std::unique_ptr"]:
            return cpp_type_to_lua_type(cpp_db, sub_types[0])
        elif cpp_type == "std::function":
            # TODO: re-use what is done in obidog.parsers.type_parser
            fun_return_type, fun_args = sub_types[0].split("(")
            fun_args = fun_args.strip().removesuffix(")").strip()
            fun_args = split_root_types(fun_args)
            fun_args_formatted = []
            for fun_arg_i, fun_arg in enumerate(fun_args):
                fun_arg = prepare_and_strip_type(fun_arg)
                fun_arg_split = split_root_types(fun_arg)
                # Is the argument name present ?
                if len(fun_arg_split) == 1 and len(fun_arg.split(" ")) == 2:
                    fun_arg_type, fun_arg_name = fun_arg.split(" ")
                    fun_args_formatted.append(
                        f"{fun_arg_name}:{cpp_type_to_lua_type(cpp_db, fun_arg_type)}"
                    )
                elif len(fun_arg_split) == 1 and len(fun_arg.split(" ")) > 2:
                    raise RuntimeError("Is that supposed to happen ?")
                else:
                    fun_args_formatted.append(
                        f"p{fun_arg_i}:{cpp_type_to_lua_type(cpp_db, fun_arg)}"
                    )
            fun_lua_return_type = cpp_type_to_lua_type(cpp_db, fun_return_type)
            fun_lua_return_type = (
                f":{fun_lua_return_type}" if fun_lua_return_type.type != "nil" else ""
            )
            fun_signature = f"fun({', '.join(fun_args_formatted)}){fun_lua_return_type}"
            lua_type = fun_signature
        elif cpp_type == "std::variant":
            lua_type = "|".join(
                [
                    str(cpp_type_to_lua_type(cpp_db, variant_elem))
                    for variant_elem in sub_types
                ]
            )
        else:
            log.warn("Unable to determine proper templated type")
            lua_type = f"{cpp_type_to_lua_type(cpp_db, cpp_type)}[{cpp_type_to_lua_type(cpp_db, templated_type)}]"
    elif cpp_type in ALL_TYPES_MATCH:
        lua_type = ALL_TYPES_MATCH[cpp_type]
    else:
        lua_type = ".".join(cpp_type.split("::"))
    return LuaType(type=lua_type)


def convert_function_types(cpp_db: CppDatabase, function: FunctionUniformModel):
    if isinstance(function, FunctionOverloadModel):
        for overload in function.overloads:
            convert_function_types(cpp_db, overload)
    else:
        function.return_type = cpp_type_to_lua_type(cpp_db, function.return_type)
        for parameter in function.parameters:
            parameter.type = cpp_type_to_lua_type(cpp_db, parameter.type)


def convert_all_types(cpp_db: CppDatabase):
    for class_value in cpp_db.classes.values():
        for constructor in class_value.constructors:
            convert_function_types(cpp_db, constructor)
        for method in class_value.methods.values():
            convert_function_types(cpp_db, method)
        for attribute in class_value.attributes.values():
            attribute.type = cpp_type_to_lua_type(cpp_db, attribute.type)
        class_value.bases = [
            cpp_type_to_lua_type(cpp_db, base) for base in class_value.bases
        ]
    for function in cpp_db.functions.values():
        convert_function_types(cpp_db, function)
    for glob in cpp_db.globals.values():
        glob.type = cpp_type_to_lua_type(cpp_db, glob.type)
    for typedef in cpp_db.typedefs.values():
        typedef.type = cpp_type_to_lua_type(cpp_db, typedef.type)
