from dataclasses import dataclass
import re
from typing import Union

from obidog.databases import CppDatabase
from obidog.models.functions import FunctionModel, FunctionOverloadModel


BASIC_TYPE_MATCH = {
    "void": "nil",
    "bool": "boolean",
    "float": "number",
    "double": "number",
    "int": "number",
    "unsigned": "number",
    "unsigned int": "number",
    "long long": "number",
    "long": "number",
    "unsigned long": "number",
    "unsigned long long": "number",
    "short": "number",
    "unsigned short": "number",
    "string": "string",
    "std::string": "string",
    "vector": "table",
    "std::vector": "table",
    "pair": "table",
    "std::pair": "table",
    "map": "table",
    "std::map": "table",
    "std::unoredered_map": "table",
    "size_t": "number",
    "std::size_t": "number",
    "std::string_view": "string",
    "std::shared_ptr": "shared_pointer",
    "std::weak_ptr": "weak_pointer",
    "std::optional": "optional",
    "std::tuple": "table",
    "std::function": "function",
    "int8_t": "number",
    "int16_t": "number",
    "int32_t": "number",
    "int64_t": "number",
    "uint8_t": "number",
    "uint16_t": "number",
    "uint32_t": "number",
    "uint64_t": "number",
    "std::int8_t": "number",
    "std::int16_t": "number",
    "std::int32_t": "number",
    "std::int64_t": "number",
    "std::uint8_t": "number",
    "std::uint16_t": "number",
    "std::uint32_t": "number",
    "std::uint64_t": "number",
    "char": "string",
}
LUA_TYPE_MATCH = {"sol::table": "table", "sol::function": "function"}
OTHER_TYPE_MATCH = {
    "Time::TimeUnit": "obe.Time.TimeUnit",
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
    "obe::Input::InputButtonState": "obe.Input.InputButtonState",
    "Canvas": "obe.Graphics.Canvas.Canvas",
    "CanvasElementType": "obe.Graphics.Canvas.CanvasElementType",
    "Cursor": "obe.System.Cursor",
    "Input::InputButtonState": "obe.Input.InputButtonState",
    "TimeUnit": "obe.Time.TimeUnit",
}
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
    type: str

    def __str__(self):
        return f"{self.type}".strip(" ")


def split_root_types(templated_type: str):
    inner_template_count = 0
    segments = []
    buffer = ""
    for char in templated_type:
        if char in ["<", "("]:
            inner_template_count += 1
            buffer = buffer + char
        elif char == [">", ")"]:
            inner_template_count -= 1
            buffer = buffer + char
        elif char == "," and not inner_template_count:
            segments.append(buffer.strip())
            buffer = ""
        else:
            buffer = buffer + char
    if buffer.strip():
        segments.append(buffer.strip())
    return [segment.strip() for segment in segments]


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
            lua_type = f"table<number, {cpp_type_to_lua_type(cpp_db, sub_types[0])}>"
        elif cpp_type in ["std::unordered_map", "std::map"]:
            lua_type = f"table<{cpp_type_to_lua_type(cpp_db, sub_types[0])}, {cpp_type_to_lua_type(cpp_db, sub_types[1])}>"
        elif cpp_type in ["std::pair", "std::tuple"]:
            if all(sub_type == sub_types[0] for sub_type in sub_types):
                lua_type = (
                    f"table<number, {cpp_type_to_lua_type(cpp_db, sub_types[0])}>"
                )
            else:
                lua_type = "table<number, any>"  # TODO: Build better generic ?
        elif cpp_type == "sol::nested":
            return cpp_type_to_lua_type(cpp_db, sub_types[0])
        elif cpp_type in ["std::shared_ptr", "std::unique_ptr"]:
            return cpp_type_to_lua_type(cpp_db, sub_types[0])
        elif cpp_type == "std::function":
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
        else:
            print("[Warning] Unable to determine proper templated type")
            lua_type = f"{cpp_type_to_lua_type(cpp_db, cpp_type)}<{cpp_type_to_lua_type(cpp_db, templated_type)}>"
    elif cpp_type in ALL_TYPES_MATCH:
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
    return LuaType(type=lua_type)
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
        for constructor in class_value.constructors:
            convert_function_types(cpp_db, constructor)
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
