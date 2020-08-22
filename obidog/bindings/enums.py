import os
from typing import List

import obidog.bindings.flavours.sol3 as flavour
from obidog.bindings.utils import fetch_table, strip_include
from obidog.logger import log
from obidog.models.enums import EnumModel
from obidog.utils.string_utils import format_name


def generate_enum_fields(enum_type: str, enum: EnumModel):
    body = []
    for enum_field in enum.values:
        body.append(f'{{"{enum_field.name}", {enum_type}::{enum_field.name}}}')
    return "{" + ",".join(body) + "}"


def generate_enums_bindings(name: str, enums: List[EnumModel]):
    includes = []
    bindings_functions = []
    objects = []
    for enum_name, enum in enums.items():
        log.info(f"  Generating bindings for enum {enum_name}")
        enum_path = strip_include(enum.location).replace(os.path.sep, "/")
        includes.append(f"#include <{enum_path}>")
        state_view = flavour.STATE_VIEW
        export_name = format_name(enum.name)
        binding_function_signature = f"void LoadEnum{export_name}({state_view} state)"
        table_access = fetch_table(name) + "\n"
        binding_function_body = table_access + flavour.ENUM_BODY.format(
            namespace=name.split("::")[-1],
            enum_type=enum_name,
            enum_name=enum.name,
            enum_fields=generate_enum_fields(enum_name, enum),
        )
        bindings_functions.append(
            f"{binding_function_signature}\n{{\n" f"{binding_function_body}\n}}"
        )
        objects.append(f"Enum{export_name}")
    return {
        "includes": includes,
        "bindings_functions": bindings_functions,
        "objects": objects,
    }
