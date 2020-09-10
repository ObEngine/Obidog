from collections import defaultdict
from obidog.config import (
    PATH_TO_OBENGINE,
    SOURCE_DIRECTORIES,
    BINDINGS_CONFIG_FILE,
    BINDINGS_SOURCES_LOCATION,
    BINDINGS_HEADERS_LOCATION,
)
from obidog.databases import CppDatabase
from obidog.bindings.flavours import sol3 as flavour
from obidog.bindings.utils import strip_include
from obidog.bindings.classes import (
    generate_classes_bindings,
    copy_parent_bindings,
    copy_parent_bases,
)
from obidog.bindings.enums import generate_enums_bindings
from obidog.bindings.functions import generate_functions_bindings
from obidog.bindings.globals import generate_globals_bindings
from obidog.logger import log
from obidog.wrappers.clangformat_wrapper import clang_format_files
from obidog.utils.string_utils import clean_capitalize
from obidog.models.functions import PlaceholderFunctionModel
import os
import inflection
import re

GENERATE_BINDINGS = False
BINDINGS_INCLUDE_TEMPLATE = """
#pragma once

namespace {state_view_forward_decl_ns} {{ class {state_view_forward_decl_cls}; }};
namespace {namespace}
{{
{bindings_functions_signatures}
}};
""".strip(
    "\n"
)

BINDINGS_SRC_TEMPLATE = """
#include <{bindings_header}>

{includes}

#include <{bindings_config_file}>

namespace {namespace}
{{
{bindings_functions}
}};
""".strip(
    "\n"
)

OUTPUT_DIRECTORY = os.environ.get("OBENGINE_BINDINGS_OUTPUT", PATH_TO_OBENGINE)


def group_bindings_by_namespace(cpp_db):
    group_by_namespace = defaultdict(CppDatabase)
    for item_type in [
        "classes",
        "enums",
        "functions",
        "globals",
        "typedefs",
    ]:
        for item_name, item_value in getattr(cpp_db, item_type).items():
            strip_template = item_name.split("<")[0]
            last_namespace = "::".join(strip_template.split("::")[:-1:])
            if last_namespace in cpp_db.namespaces:
                getattr(group_by_namespace[last_namespace], item_type)[
                    item_name
                ] = item_value
    for namespace_name, namespace in group_by_namespace.items():
        namespace.namespaces = cpp_db.namespaces[namespace_name]
    return group_by_namespace


def make_bindings_header(path, namespace, objects):
    inc_out = os.path.join(OUTPUT_DIRECTORY, "include", "Core", path)
    state_view = flavour.STATE_VIEW
    bindings_functions = [
        f"void Load{object_name['bindings']}({state_view} state);"
        for object_name in objects
    ]
    with open(inc_out, "w") as class_binding:
        class_binding.write(
            BINDINGS_INCLUDE_TEMPLATE.format(
                namespace=f"{namespace}::Bindings",
                bindings_functions_signatures="\n".join(
                    f"{binding_function}" for binding_function in bindings_functions
                ),
                state_view_forward_decl_ns="::".join(state_view.split("::")[:-1:]),
                state_view_forward_decl_cls=state_view.split("::")[-1],
            )
        )


def make_bindings_sources(namespace, path, bindings_header, *datasets):
    src_out = os.path.join(OUTPUT_DIRECTORY, "src", "Core", path)
    with open(src_out, "w") as bindings_source:
        all_includes = set(
            includes
            for data in datasets
            for includes in data["includes"]
            if not includes.endswith(".cpp")
        )
        all_functions = [
            functions for data in datasets for functions in data["bindings_functions"]
        ]
        bindings_source.write(
            BINDINGS_SRC_TEMPLATE.format(
                bindings_header=bindings_header,
                bindings_config_file=BINDINGS_CONFIG_FILE,
                namespace=f"{namespace}::Bindings",
                includes="\n".join(all_includes),
                bindings_functions="\n".join(all_functions),
            )
        )


FILES_TO_FORMAT = []


def generate_bindings_for_namespace(name, namespace):
    log.info(f"Generating bindings for namespace {name}")
    split_name = "/".join(name.split("::"))
    base_path = f"Bindings/{split_name}"
    os.makedirs(
        os.path.join(OUTPUT_DIRECTORY, "include", "Core", base_path), exist_ok=True
    )
    os.makedirs(os.path.join(OUTPUT_DIRECTORY, "src", "Core", base_path), exist_ok=True)

    class_bindings = generate_classes_bindings(namespace.classes)
    enum_bindings = generate_enums_bindings(name, namespace.enums)
    functions_bindings = generate_functions_bindings(namespace.functions)
    globals_bindings = generate_globals_bindings(name, namespace.globals)

    generated_objects = (
        class_bindings["objects"]
        + enum_bindings["objects"]
        + functions_bindings["objects"]
        + globals_bindings["objects"]
    )

    bindings_header = os.path.join(base_path, f"{name.split('::')[-1]}.hpp").replace(
        os.path.sep, "/"
    )
    if GENERATE_BINDINGS:
        make_bindings_header(bindings_header, name, generated_objects)
    namespace_data = {
        "includes": namespace.namespaces.flags.additional_includes
        if namespace.namespaces.flags.additional_includes
        else [],
        "bindings_functions": [],
    }
    bindings_source = os.path.join(base_path, f"{name.split('::')[-1]}.cpp").replace(
        os.path.sep, "/"
    )
    FILES_TO_FORMAT.append(os.path.join(BINDINGS_HEADERS_LOCATION, bindings_header))
    FILES_TO_FORMAT.append(os.path.join(BINDINGS_SOURCES_LOCATION, bindings_source))
    if GENERATE_BINDINGS:
        make_bindings_sources(
            name,
            bindings_source,
            bindings_header,
            enum_bindings,
            class_bindings,
            functions_bindings,
            globals_bindings,
            namespace_data,
        )
    return generated_objects, bindings_header, bindings_source


def fetch_sub_dict(d, path):
    if len(path) == 0:
        return d
    if len(path) > 1:
        return fetch_sub_dict(d[path[0]], path[1::])
    else:
        return d[path[0]]


BINDTREE_NEWTABLE = 'BindTree{fetch_table}.add("{last_table}", InitTreeNodeAsTable("{intermediate_table}"));'


def fix_index_tables(tables):
    # Pre-sort the table to fix missing intermediate tables
    tables.sort(key=lambda x: x.count("["))
    table_tree = {}
    for table in tables:
        table_path = re.findall(r'(?:\[\"([^"]+)\"\])', table)
        for i, elem in enumerate(table_path):
            if not elem in fetch_sub_dict(table_tree, table_path[:i]):
                if i != len(table_path) - 1:
                    print("Add missing intermediate table", ".".join(table_path))
                    namespace_full_path = "".join(
                        [f'["{item}"]' for item in table_path[: i + 1]]
                    )
                    tables.append(
                        f"state{namespace_full_path}.get_or_create<sol::table>();"
                    )
                fetch_sub_dict(table_tree, table_path[:i])[table_path[i]] = {}
    # Don't load a sub-table before the main one
    tables.sort(key=lambda x: x.count("["))


# LATER: Generate bindings shorthands
def generated_bindings_index(generated_objects):
    print("Generating Bindings Index...")
    body = []
    include_list = []
    for current_dir, folders, files in os.walk(
        os.path.join(OUTPUT_DIRECTORY, BINDINGS_HEADERS_LOCATION, "Bindings")
    ):
        for f in files:
            if f.endswith(".hpp"):
                fp = (
                    os.path.join(current_dir, f)
                    .split(OUTPUT_DIRECTORY)[1]
                    .lstrip("/\\")
                )
                include_list.append(strip_include(fp).replace("\\", "/"))
    body += [f"#include <{path}>" for path in include_list]
    body += [
        f"#include <{flavour.INCLUDE_FILE}>",
        "namespace obe::Bindings {",
        f"void IndexAllBindings({flavour.STATE_VIEW} state)\n{{",
    ]

    tables = []
    bindings = []
    for namespace_name, objects in generated_objects.items():
        ns_split = namespace_name.split("::")
        namespace_full_path = "".join(
            f'["{namespace_part}"]' for namespace_part in ns_split
        )
        tables.append(f"state{namespace_full_path}.get_or_create<sol::table>();")

        print(objects)
        for generated_object in objects["objects"]:
            bindings.append(
                f"{namespace_name}::Bindings::Load{generated_object}(state);"
            )
        bindings.append("\n")
    fix_index_tables(tables)
    body += tables
    body += bindings
    body.append("}}")
    return "\n".join(body)


def apply_proxies(cpp_db, functions):
    all_functions = {
        **cpp_db.functions,
        **{
            f"{class_name}::{method_name}": method_value
            for class_name, class_value in cpp_db.classes.items()
            for method_name, method_value in class_value.methods.items()
        },
    }
    for function_value in functions.values():
        if function_value.flags.proxy:
            patch = all_functions[function_value.flags.proxy]
            patch.definition = function_value.definition
            patch.parameters = function_value.parameters
            patch.return_type = function_value.return_type
            patch.location = function_value.location
            patch.replacement = function_value.definition.split()[1]


def discard_placeholders(cpp_db):
    for class_value in cpp_db.classes.values():
        class_value.methods = {
            method_name: method
            for method_name, method in class_value.methods.items()
            if not isinstance(method, PlaceholderFunctionModel)
        }
    cpp_db.functions = {
        function_name: function
        for function_name, function in cpp_db.functions.items()
        if not isinstance(function, PlaceholderFunctionModel)
    }


# LATER: Add a tag in Doxygen to allow custom name / namespace binding
# LATER: Add a tag in Doxygen to list possible templated types
# LATER: Add a tag in Doxygen to make fields privates
# TODO: Add a tag in Doxygen to specify a helper script
# OR add a way to define a list of helpers (lua scripts) to run for some namespaces
# TODO: Check if it's possible to change a bound global value from Lua, otherwise provide a lambda setter
# LATER: Provide a way to "patch" some namespaces / classes / functions with callbacks
# LATER: Provide a "policy" system to manage bindings grouping etc...
# LATER: Try to shorten function pointers / full names given the namespace we are in while binding
# TODO: Check behaviour with std::optional, std::variant, std::any (getSegmentContainingPoint for example)
# TODO: Check behaviour with smart pointers
# TODO: Allow injection of "commonly used types" in templated functions using a certain flag in doc (pushParameter for example)
def generate_bindings(cpp_db, write_files: bool = True):
    global GENERATE_BINDINGS
    GENERATE_BINDINGS = write_files
    log.info("===== Generating bindings for ÖbEngine ====")
    discard_placeholders(cpp_db)
    namespaces = group_bindings_by_namespace(cpp_db)
    generated_objects = {}
    for namespace_name, namespace in namespaces.items():
        copy_parent_bindings(cpp_db, namespace.classes)
        copy_parent_bases(cpp_db, namespace.classes)
        apply_proxies(cpp_db, namespace.functions)
        generation_results = generate_bindings_for_namespace(namespace_name, namespace)
        generated_objects[namespace_name] = {
            "objects": generation_results[0],
            "header": generation_results[1],
            "source": generation_results[2],
        }
    if GENERATE_BINDINGS:
        with open(
            os.path.join(
                OUTPUT_DIRECTORY, f"{BINDINGS_SOURCES_LOCATION}/Bindings/index.cpp"
            ),
            "w",
        ) as bindings_index:
            bindings_index.write(generated_bindings_index(generated_objects))
    FILES_TO_FORMAT.append(f"{BINDINGS_SOURCES_LOCATION}/Bindings/index.cpp")
    if GENERATE_BINDINGS:
        clang_format_files(FILES_TO_FORMAT)
    return generated_objects
