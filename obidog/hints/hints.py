import os
import re
from typing import Dict, List, Union

from mako.template import Template
from mako.lookup import TemplateLookup
from obidog.bindings.generator import discard_placeholders

from obidog.converters.lua.types import LuaType, convert_all_types
from obidog.databases import CppDatabase
from obidog.logger import log
from obidog.models.classes import AttributeModel, ClassModel
from obidog.models.functions import FunctionModel
from obidog.models.namespace import NamespaceModel
from obidog.models.qualifiers import QualifiersModel

ALIASES = {
    "obe.Time.TimeUnit": "number",
    "obe.Animation.Easing.Easing.EasingFunction": "function",
    "obe.Collision.TrajectoryCheckFunction": "function(trajectory: obe.Collision.Trajectory, offset: obe.Transform.UnitVector, collider: obe.Collision.PolygonalCollider)",
    "obe.Collision.OnCollideCallback": "function(trajectory: obe.Collision.Trajectory, offset: obe.Transform.UnitVector, data: obe.Collision.CollisionData)",
    "obe.Event.Callback": "function",
    "obe.Event.ExternalEventListener": "obe.Event.LuaEventListener",
    "obe.Event.EventProfiler": "table<string, obe.Event.CallbackProfiler>",
    "obe.Event.OnListenerChange": "function(change_state: obe.Event.ListenerChangeState, string)",
    "obe.Event.EventGroupPtr": "obe.Event.EventGroup",
    "sol.protected_function": "function",
    "sol.lua_value": "any",
    "sol.object": "table",
    "obe.Graphics.CoordinateTransformer": "function(position: number, camera: number, layer: number):number",
    "obe.System.MountList": "table<number, obe.System.MountablePath>",
    "obe.Tiles.AnimatedTiles": "table<number, obe.Tiles.AnimatedTile>",
    "obe.Transform.PolygonPath": "table<number, obe.Transform.PolygonPoint>",
    "obe.Transform.point_index_t": "number",
    "point_index_t": "number",
    "vili.number": "number",
    "vili.integer": "number",
    "vili.boolean": "boolean",
    "vili.array": "table<number, any>",
    "vili.object": "table<string, any>",
    "vili.string": "string",
    "obe.Input.InputButtonMonitorPtr": "obe.Input.InputButtonMonitor",
}

# TODO: add the Event table as a type
# TODO: rename p0, p1, p2 to proper parameter names

MANUAL_TYPES = {"Engine": "obe.Engine.Engine", "This": "obe.Script.GameObject"}


def write_hints(
    tables: List[str],
    elements: List[Union[ClassModel, NamespaceModel, FunctionModel, AttributeModel]],
):
    lookup = TemplateLookup(["templates/hints"])
    with open("templates/hints/lua_class.mako", "r", encoding="utf-8") as tpl:
        class_tpl = Template(tpl.read(), lookup=lookup)
    with open("templates/hints/lua_function.mako", "r", encoding="utf-8") as tpl:
        function_tpl = Template(tpl.read(), lookup=lookup)
    with open("templates/hints/lua_enum.mako", "r", encoding="utf-8") as tpl:
        enum_tpl = Template(tpl.read(), lookup=lookup)
    with open("templates/hints/lua_global.mako", "r", encoding="utf-8") as tpl:
        global_tpl = Template(tpl.read(), lookup=lookup)
    hints = [f"{table} = {{}};\n" for table in tables]
    hints += ["\n"]
    hints += [
        f"---@alias {alias_from} {alias_to}\n\n"
        for alias_from, alias_to in ALIASES.items()
    ]
    for element in elements:
        if element._type == "class":
            hints.append(class_tpl.get_def("lua_class").render(klass=element))
        elif element._type == "function":
            hints.append(function_tpl.get_def("lua_function").render(function=element))
        elif element._type == "enum":
            hints.append(enum_tpl.get_def("lua_enum").render(enum=element))
        elif element._type == "global":
            hints.append(global_tpl.get_def("lua_global").render(glob=element))
    hints += ["\n\n"]
    hints += [
        f"---@type {manual_type_value}\n{manual_type_name} = {{}};\n\n"
        for manual_type_name, manual_type_value in MANUAL_TYPES.items()
    ]
    with open(
        os.path.join("export", "hints.lua"),
        "w",
        encoding="utf-8",
    ) as export:
        export.write("".join(hints))


def _add_return_type_to_constructors(cpp_db: CppDatabase):
    for class_value in cpp_db.classes.values():
        for constructor in class_value.constructors:
            lua_class_name = (
                f"{class_value.namespace.replace('::', '.')}.{class_value.name}"
            )
            constructor.return_type = LuaType(type=lua_class_name)
            if not constructor.description:
                constructor.description = f"{lua_class_name} constructor"


def _remove_operators(cpp_db: CppDatabase):
    for class_value in cpp_db.classes.values():
        operators_to_pop = []
        for method_name, method in class_value.methods.items():
            if re.search(r"^operator\W", method.name):
                operators_to_pop.append(method_name)
        for method_name in operators_to_pop:
            class_value.methods.pop(method_name)


def _get_namespace_tables(elements):
    return sorted(
        list(
            set(
                [
                    element.namespace.replace("::", ".")
                    for element in elements
                    if hasattr(element, "namespace") and element.namespace
                ]
            )
        ),
        key=lambda s: s.count("."),
    )


def _fix_bind_as(elements: List[Union[FunctionModel, ClassModel, AttributeModel]]):
    for element in elements:
        if element.flags.bind_to:
            element.name = element.flags.bind_to
        if isinstance(element, ClassModel):
            _fix_bind_as(element.methods.values())
            _fix_bind_as(element.attributes.values())


def _setup_methods_as_attributes(classes: Dict[str, ClassModel]):
    for class_value in classes.values():
        methods_to_pop = []
        for method_name, method in class_value.methods.items():
            if method.flags.as_property:
                methods_to_pop.append(method_name)
                class_value.attributes[method.name] = AttributeModel(
                    name=method.name,
                    namespace=method.namespace,
                    type=method.return_type,
                    qualifiers=QualifiersModel(
                        method.qualifiers.const, method.qualifiers.static
                    ),
                    description=method.description,
                    flags=method.flags,
                    export=method.export,
                    location=method.location,
                    visibility=method.visibility,
                    urls=method.urls,
                )
        for method in methods_to_pop:
            class_value.methods.pop(method)


def generate_hints(cpp_db: CppDatabase):
    log.info("Discarding placeholders")
    discard_placeholders(cpp_db)

    log.info("Converting all types")
    convert_all_types(cpp_db)

    all_elements = [
        item
        for item_type in cpp_db.__dict__.keys()
        for item in getattr(cpp_db, item_type).values()
        if not item.flags.nobind
    ]

    _add_return_type_to_constructors(cpp_db)
    _remove_operators(cpp_db)

    _fix_bind_as(all_elements)
    _setup_methods_as_attributes(cpp_db.classes)

    log.info("Generating hints")
    write_hints(_get_namespace_tables(all_elements), all_elements)
