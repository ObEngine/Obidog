from collections import defaultdict
import glob
import os
import re
import shutil
from typing import Dict, List, Union

from mako.template import Template
from mako.lookup import TemplateLookup
from obidog.bindings.generator import discard_placeholders

from obidog.config import PATH_TO_OBENGINE
from obidog.converters.lua.types import LuaType, convert_all_types
from obidog.databases import CppDatabase
from obidog.logger import log
from obidog.models.classes import AttributeModel, ClassModel
from obidog.models.functions import FunctionModel
from obidog.models.namespace import NamespaceModel
from obidog.models.qualifiers import QualifiersModel
from obidog.converters.lua.types import DYNAMIC_TYPES, DynamicTupleType

# TODO: rename p0, p1, p2 to proper parameter names


BindableElement = Union[ClassModel, NamespaceModel, FunctionModel, AttributeModel]

EVENT_NAMESPACE = "events"


def write_hints(
    elements_by_namespace: Dict[str, List[BindableElement]],
):
    lookup = TemplateLookup(["templates/hints"])
    export_directory = os.path.join(PATH_TO_OBENGINE, "engine", "Hints")

    # Load hints templates
    templates = {}
    with open("templates/hints/lua_class.mako", "r", encoding="utf-8") as tpl:
        templates["class"] = Template(tpl.read(), lookup=lookup)
    with open("templates/hints/lua_function.mako", "r", encoding="utf-8") as tpl:
        templates["function"] = Template(tpl.read(), lookup=lookup)
    with open("templates/hints/lua_enum.mako", "r", encoding="utf-8") as tpl:
        templates["enum"] = Template(tpl.read(), lookup=lookup)
    with open("templates/hints/lua_global.mako", "r", encoding="utf-8") as tpl:
        templates["global"] = Template(tpl.read(), lookup=lookup)
    with open("templates/hints/lua_typedef.mako", "r", encoding="utf-8") as tpl:
        templates["typedef"] = Template(tpl.read(), lookup=lookup)

    # Build hint list for each namespace
    hints_by_namespace = {namespace: [] for namespace in elements_by_namespace}

    # Add initial table declaration on top of each namespace
    for namespace, hints in hints_by_namespace.items():
        hints.append("---@meta\n\n")
        if namespace:
            hints.append(f"{namespace} = {{}};\n")

    # Render all hints
    for namespace, elements in elements_by_namespace.items():
        for element in elements:
            if element._type in templates:
                element_tpl = templates[element._type]
                rendered_element = element_tpl.get_def("render").render(element=element)
                hints_by_namespace[namespace].append(rendered_element)

    # Add "return" statement at end of module
    for namespace, hints in hints_by_namespace.items():
        if namespace:
            hints.append(f"return {namespace};")

    # Copy custom hints to export folder
    for custom_hint_filename in glob.glob(os.path.join("hints", "*.*")):
        shutil.copy(custom_hint_filename, export_directory)

    for namespace, hints in hints_by_namespace.items():
        namespace_name = namespace if namespace else "_root"
        with open(
            os.path.join(export_directory, f"{namespace_name}.lua"),
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


def _group_elements_by_namespace(elements):
    elements_by_namespace = {
        namespace: [] for namespace in _get_namespace_tables(elements)
    }
    # Elements without namespace
    elements_by_namespace[""] = []
    for element in elements:
        dotted_namespace = ""
        if hasattr(element, "namespace") and element.namespace:
            dotted_namespace = element.namespace.replace("::", ".")
        elements_by_namespace[dotted_namespace].append(element)

    return elements_by_namespace


def _fix_bind_as(elements: List[Union[FunctionModel, ClassModel, AttributeModel]]):
    for element in elements:
        if element.flags.rename:
            element.name = element.flags.rename
            if element._type == "overload":
                for overload in element.overloads:
                    overload.name = element.flags.rename
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
                    description=method.description or "",
                    flags=method.flags,
                    export=method.export,
                    location=method.location,
                    visibility=method.visibility,
                    urls=method.urls,
                )
        for method in methods_to_pop:
            class_value.methods.pop(method)


def _build_table_for_events(classes: Dict[str, ClassModel]):
    result = {}
    events = []
    for class_value in classes.values():
        if class_value.namespace.startswith(f"obe::{EVENT_NAMESPACE}::"):
            events.append(class_value)
    events_grouped_by_section = defaultdict(list)
    for event in events:
        if "id" not in event.attributes:
            continue
        event_initializer = event.attributes["id"].initializer or ""
        event_id = (
            event_initializer.strip()
            .removeprefix("=")
            .strip()
            .removeprefix('"')
            .removesuffix('"')
        )
        events_grouped_by_section[
            event.namespace.removeprefix(f"obe::{EVENT_NAMESPACE}::")
        ].append((event_id, event))

    event_groups = {}
    for event_group_name, events in events_grouped_by_section.items():
        event_group_attributes = {
            event_id: AttributeModel(
                name=event_id,
                type=LuaType(f"fun(evt:obe.events.{event_group_name}.{event.name})"),
                namespace=event.namespace,
            )
            for event_id, event in events
        }
        event_groups[event_group_name] = ClassModel(
            name=event_group_name,
            namespace=f"obe::{EVENT_NAMESPACE}::_EventTableGroups",
            attributes=event_group_attributes,
            constructors=[],
            methods={},
        )

    event_groups_as_attributes = {}
    for event_group_name, event_group in event_groups.items():
        event_groups_as_attributes[event_group_name] = AttributeModel(
            name=event_group.name,
            namespace=event_group.namespace,
            type=LuaType(f"obe.{EVENT_NAMESPACE}._EventTableGroups.{event_group_name}"),
        )

    event_namespace = ClassModel(
        name="_EventTable",
        namespace=f"obe::{EVENT_NAMESPACE}",
        attributes=event_groups_as_attributes,
        constructors=[],
        methods={},
    )

    for event_group_name, event_group in event_groups.items():
        result[f"{event_group.namespace}::{event_group.name}"] = event_group
    result[f"obe::{EVENT_NAMESPACE}::_EventTable"] = event_namespace

    return result


def _generate_dynamic_tuple(
    tuple_name: str, tuple_type: DynamicTupleType
) -> ClassModel:
    return ClassModel(
        tuple_name,
        "",
        attributes={
            f"[{i}]": AttributeModel(
                name=f"[{i}]",
                type=sub_type,
                namespace="",
            )
            for i, sub_type in enumerate(tuple_type.sub_types)
        },
        constructors=[],
        methods={},
    )


def _generate_dynamic_types() -> Dict[str, ClassModel]:
    result = {}
    for dynamic_type_name, dynamic_type in DYNAMIC_TYPES.dynamic_types.items():
        if isinstance(dynamic_type, DynamicTupleType):
            result[dynamic_type_name] = _generate_dynamic_tuple(
                dynamic_type_name, dynamic_type
            )
    return result


def generate_hints(cpp_db: CppDatabase, path_to_doc: str):
    log.info("Discarding placeholders")
    discard_placeholders(cpp_db)

    log.info("Converting all types")
    convert_all_types(cpp_db)

    cpp_db.classes |= _build_table_for_events(cpp_db.classes)
    cpp_db.classes |= _generate_dynamic_types()
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
    write_hints(_group_elements_by_namespace(all_elements))
