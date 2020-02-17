from collections import defaultdict
from obidog.databases import CppDatabase
from obidog.bindings.flavours import sol3 as flavour
from obidog.bindings.utils import strip_include
from obidog.bindings.classes import generate_classes_bindings
from obidog.bindings.enums import generate_enums_bindings
from obidog.logger import log
import os


BINDINGS_INCLUDE_TEMPLATE = """
#pragma once

namespace {state_view_forward_decl_ns} {{ class {state_view_forward_decl_cls}; }};
namespace {namespace}
{{
{bindings_functions_signatures};
}};
""".strip(
    "\n"
)

# TODO: Classes on separate file is ok, add one file for enums + functions etc...

BINDINGS_SRC_TEMPLATE = """
#include <{bindings_header}>
#include <{bindings_lib}>

{includes}

namespace {namespace}
{{
{bindings_functions}
}};
""".strip(
    "\n"
)


def group_bindings_by_namespace(cpp_db):
    group_by_namespace = defaultdict(CppDatabase)
    for item_type in ["classes", "enums", "functions", "globals", "typedefs"]:
        for item_name, item_value in getattr(cpp_db, item_type).items():
            strip_template = item_name.split("<")[0]
            last_namespace = "::".join(strip_template.split("::")[:-1:])
            getattr(group_by_namespace[last_namespace], item_type)[
                item_name
            ] = item_value
    return group_by_namespace


def make_bindings_header(path, namespace, objects):
    inc_out = os.path.join("output", "include", path)
    state_view = flavour.STATE_VIEW
    bindings_functions = [
        f"void Load{object_name}({state_view} state)" for object_name in objects
    ]
    with open(inc_out, "w") as class_binding:
        class_binding.write(
            BINDINGS_INCLUDE_TEMPLATE.format(
                namespace=f"{namespace}::Bindings",
                bindings_functions_signatures="\n".join(bindings_functions),
                state_view_forward_decl_ns="::".join(state_view.split("::")[:-1:]),
                state_view_forward_decl_cls=state_view.split("::")[-1],
            )
        )


def make_bindings_sources(namespace, path, bindings_header, *datasets):
    with open(path, "w") as bindings_source:
        all_includes = set(includes for data in datasets for includes in data["includes"])
        all_functions = [
            functions for data in datasets for functions in data["bindings_functions"]
        ]
        bindings_source.write(
            BINDINGS_SRC_TEMPLATE.format(
                bindings_header=bindings_header,
                bindings_lib=flavour.INCLUDE_FILE,
                namespace=f"{namespace}::Bindings",
                includes="\n".join(all_includes),
                bindings_functions="\n".join(all_functions),
            )
        )


def generate_bindings_for_namespace(name, namespace):
    log.info(f"Generating bindings for namespace {name}")
    split_name = "/".join(name.split("::")[1::]) if "::" in name else name.capitalize()
    base_path = f"Bindings/{split_name}"
    os.makedirs(os.path.join("output", "include", base_path), exist_ok=True)
    os.makedirs(os.path.join("output", "src", base_path), exist_ok=True)
    class_bindings = generate_classes_bindings(namespace.classes, base_path)
    enum_bindings = generate_enums_bindings(name, namespace.enums, base_path)

    bindings_header = os.path.join(
        base_path,
        f"{name.split('::')[-1]}.hpp"
    ).replace(os.path.sep, "/")

    make_bindings_header(
        bindings_header, name, class_bindings["objects"] + enum_bindings["objects"]
    )
    src_out = os.path.join("output", "src", base_path, f"{name.split('::')[-1]}.cpp")
    make_bindings_sources(name, src_out, bindings_header, enum_bindings, class_bindings)


def generate_bindings(cpp_db):
    log.info("===== Generating bindings for ÖbEngine ====")
    namespaces = group_bindings_by_namespace(cpp_db)
    for namespace_name, namespace in namespaces.items():
        generate_bindings_for_namespace(namespace_name, namespace)
