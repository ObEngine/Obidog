import os
import re
from typing import List, Union

from bs4 import BeautifulSoup
from mako.template import Template
from mako.lookup import TemplateLookup
from mako import exceptions
from obidog.bindings.generator import discard_placeholders

from obidog.converters.lua.types import LuaType, convert_all_types
from obidog.databases import CppDatabase
from obidog.logger import log
from obidog.models.classes import AttributeModel, ClassModel
from obidog.models.functions import FunctionModel
from obidog.models.namespace import NamespaceModel


def write_hints(
    elements: List[Union[ClassModel, NamespaceModel, FunctionModel, AttributeModel]]
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
    hints = []
    for element in elements:
        if element._type == "class":
            hints.append(class_tpl.get_def("lua_class").render(klass=element))
        elif element._type == "function":
            hints.append(function_tpl.get_def("lua_function").render(function=element))
        elif element._type == "enum":
            hints.append(enum_tpl.get_def("lua_enum").render(enum=element))
        elif element._type == "global":
            hints.append(global_tpl.get_def("lua_global").render(glob=element))
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
            constructor.return_type = LuaType(
                type=lua_class_name,
                prefix="",
                suffix="",
            )
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

    log.info("Generating hints")
    write_hints(all_elements)
