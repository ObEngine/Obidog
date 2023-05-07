from dataclasses import dataclass
import os
import re
from collections import defaultdict
from types import FunctionType
from typing import Union

from obidog.bindings.classes import (
    apply_inherit_hook,
    copy_parent_bases,
    copy_parent_bindings,
    generate_class_template_specialisations,
    generate_classes_bindings,
    flag_abstract_classes,
)
from obidog.bindings.enums import generate_enums_bindings
from obidog.bindings.flavours import sol3 as flavour
from obidog.bindings.functions import generate_functions_bindings
from obidog.bindings.globals import generate_globals_bindings
from obidog.bindings.utils import strip_include, strip_qualifiers_from_type
from obidog.config import (
    BINDINGS_CONFIG_FILE,
    PATH_TO_OBENGINE,
    SOURCE_DIRECTORIES,
    SOURCE_DIRECTORIES_BY_OUTPUT,
    LOCATIONS,
)
from obidog.databases import CppDatabase
from obidog.logger import log
from obidog.models.flags import MetaTag
from obidog.models.functions import (
    FunctionModel,
    FunctionOverloadModel,
    FunctionPlaceholderModel,
    FunctionUniformModel,
)
from obidog.models.namespace import NamespaceModel
from obidog.parsers.utils.cpp_utils import parse_definition
from obidog.parsers.type_parser import parse_cpp_type
from obidog.utils.cpp_utils import make_fqn
from obidog.utils.string_utils import format_filename, format_name
from obidog.wrappers.clangformat_wrapper import clang_format_files

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


def match_namespace_with_source(namespace):
    if namespace == "":
        return "root.cpp"
    return sorted(
        [
            source
            for source in SOURCE_DIRECTORIES
            if source["namespace"] is not None
            and namespace.startswith(source["namespace"])
        ],
        key=lambda source: len(source["namespace"]),
        reverse=True,
    )[0]


def group_bindings_by_namespace(cpp_db: CppDatabase):
    group_by_namespace = defaultdict(NamespaceModel)
    for item_type in [
        "classes",
        "enums",
        "functions",
        "globals",
        "typedefs",
        "namespaces",
    ]:
        for item_name, item_value in getattr(cpp_db, item_type).items():
            strip_template = item_name.split("<")[0]
            last_namespace = "::".join(strip_template.split("::")[:-1:])
            run_once_for_root_namespace = item_name != ""  # ignore root namespace
            while last_namespace or run_once_for_root_namespace:
                run_once_for_root_namespace = False
                if last_namespace in cpp_db.namespaces:
                    getattr(group_by_namespace[last_namespace], item_type)[
                        item_name
                    ] = item_value
                    break
                else:
                    last_namespace = "::".join(last_namespace.split("::")[:-1:])
    for namespace_name, namespace in group_by_namespace.items():
        # Filling missing information
        namespace.description = cpp_db.namespaces[namespace_name].description
        namespace.name = cpp_db.namespaces[namespace_name].name
        namespace.namespace = cpp_db.namespaces[namespace_name].namespace
        namespace.path = cpp_db.namespaces[namespace_name].path
        namespace.urls = cpp_db.namespaces[namespace_name].urls
        namespace.flags = cpp_db.namespaces[namespace_name].flags
    return group_by_namespace


def make_bindings_header(path, namespace, objects):
    source = match_namespace_with_source(namespace)
    location = LOCATIONS[source["output_location"]]["headers"]
    inc_out = os.path.join(OUTPUT_DIRECTORY, location, path)
    state_view = flavour.STATE_VIEW
    bindings_functions = [
        f"void load_{object_name['bindings']}({state_view} state);"
        for object_name in objects
    ]
    with open(inc_out, "w") as class_binding:
        class_binding.write(
            BINDINGS_INCLUDE_TEMPLATE.format(
                namespace=f"{namespace}::bindings",
                bindings_functions_signatures="\n".join(
                    f"{binding_function}" for binding_function in bindings_functions
                ),
                state_view_forward_decl_ns="::".join(state_view.split("::")[:-1:]),
                state_view_forward_decl_cls=state_view.split("::")[-1],
            )
        )


FILES_TO_FORMAT = []


def make_bindings_sources(namespace, path, bindings_header, *datasets):
    source = match_namespace_with_source(namespace)
    location = LOCATIONS[source["output_location"]]["sources"]
    if source["structure_policy"] == "namespaces":
        src_out = os.path.join(OUTPUT_DIRECTORY, location, path)
        with open(src_out, "w") as bindings_source:
            all_includes = set(
                includes
                for data in datasets
                for includes in data["includes"]
                if not includes.endswith(".cpp")
            )
            all_functions = [
                functions
                for data in datasets
                for functions in data["bindings_functions"]
            ]
            bindings_source.write(
                BINDINGS_SRC_TEMPLATE.format(
                    bindings_header=bindings_header,
                    bindings_config_file=BINDINGS_CONFIG_FILE,
                    namespace=f"{namespace}::bindings",
                    includes="\n".join(all_includes),
                    bindings_functions="\n".join(all_functions),
                )
            )
    elif source["structure_policy"] == "classes":
        elements = [
            {**obj, "body": binding_function, "includes": includes}
            for dataset in datasets
            if "objects" in dataset
            for obj, binding_function, includes in zip(
                dataset["objects"], dataset["bindings_functions"], dataset["includes"]
            )
        ]
        for element in elements:
            element_path = "/".join(element["identifier"].split("::")[1::])
            src_out_base = os.path.join(
                OUTPUT_DIRECTORY,
                location,
                os.path.dirname(path),
                os.path.dirname(element_path),
            )
            src_filename = os.path.basename(element_path)
            src_out = os.path.join(src_out_base, f"{format_filename(src_filename)}.cpp")
            os.makedirs(src_out_base, exist_ok=True)
            with open(src_out, "w") as bindings_source:
                bindings_source.write(
                    BINDINGS_SRC_TEMPLATE.format(
                        bindings_header=bindings_header,
                        bindings_config_file=BINDINGS_CONFIG_FILE,
                        namespace=f"{namespace}::bindings",
                        includes=element["includes"]
                        if not element["includes"].endswith(".cpp")
                        else "",
                        bindings_functions=element["body"],
                    )
                )
            FILES_TO_FORMAT.append(src_out)


def generate_bindings_for_namespace(
    cpp_db: CppDatabase, namespace_name: str, namespace: NamespaceModel
):
    log.info(f"Generating bindings for namespace {namespace_name}")
    split_name = "/".join(namespace_name.split("::"))
    source = match_namespace_with_source(namespace_name)
    location = LOCATIONS[source["output_location"]]
    os.makedirs(
        os.path.join(OUTPUT_DIRECTORY, location["headers"], split_name),
        exist_ok=True,
    )
    os.makedirs(
        os.path.join(OUTPUT_DIRECTORY, location["sources"], split_name),
        exist_ok=True,
    )

    class_bindings = generate_classes_bindings(cpp_db, namespace.classes)
    enum_bindings = generate_enums_bindings(namespace_name, namespace.enums)
    functions_bindings = generate_functions_bindings(cpp_db, namespace.functions)
    globals_bindings = generate_globals_bindings(namespace_name, namespace.globals)

    generated_objects = (
        class_bindings["objects"]
        + enum_bindings["objects"]
        + functions_bindings["objects"]
        + globals_bindings["objects"]
    )

    bindings_header = os.path.join(
        split_name, f"{format_filename(namespace_name.split('::')[-1])}.hpp"
    ).replace(os.path.sep, "/")
    if GENERATE_BINDINGS:
        make_bindings_header(bindings_header, namespace_name, generated_objects)
    namespace_data = {
        "includes": namespace.flags.additional_includes
        if namespace.flags.additional_includes
        else [],
        "bindings_functions": [],
    }
    bindings_source = os.path.join(
        split_name, f"{format_filename(namespace_name.split('::')[-1])}.cpp"
    ).replace(os.path.sep, "/")
    FILES_TO_FORMAT.append(os.path.join(location["headers"], bindings_header))
    FILES_TO_FORMAT.append(os.path.join(location["sources"], bindings_source))
    if GENERATE_BINDINGS:
        bindings_header_include_path = strip_include(
            os.path.join(location["headers"], bindings_header)
        ).replace("\\", "/")
        make_bindings_sources(
            namespace_name,
            bindings_source,
            bindings_header_include_path,
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
            if elem not in fetch_sub_dict(table_tree, table_path[:i]):
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


@dataclass
class BindingIndexEntry:
    code: str
    priority: int


# LATER: Generate bindings shorthands
def generated_bindings_index(source_name, generated_objects):
    print("Generating Bindings Index...")
    body = []
    include_list = []
    bindings_headers_location = LOCATIONS[source_name]["headers"]
    for current_dir, _, files in os.walk(
        os.path.join(OUTPUT_DIRECTORY, bindings_headers_location)
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
        "namespace obe::bindings {",
        f"void index_{format_name(source_name)}_bindings({flavour.STATE_VIEW} state)\n{{",
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
                BindingIndexEntry(
                    code=f"{namespace_name}::bindings::load_{generated_object['bindings']}(state);",
                    priority=generated_object["load_priority"],
                )
            )

    sorted_bindings = sorted(bindings, key=lambda entry: entry.priority, reverse=True)
    bindings_code = ["\n"] + [entry.code for entry in sorted_bindings]
    fix_index_tables(tables)
    body += tables
    body += bindings_code
    body.append("}}")
    return "\n".join(body)


def apply_proxies(cpp_db: CppDatabase, functions):
    def find_and_requalify_if_needed(
        proxy_name: str, base_function_model: FunctionModel
    ) -> FunctionModel:
        def requalify_if_needed(proxy_func: FunctionUniformModel) -> FunctionModel:
            if isinstance(proxy_func, FunctionOverloadModel):
                return FunctionModel(
                    name=proxy_func.name,
                    namespace=proxy_func.namespace,
                    definition=base_function_model.return_type,
                    parameters=[],
                    from_class=proxy_func.from_class,
                    return_type=base_function_model.return_type,
                )
            return proxy_func

        if proxy_name in cpp_db.functions:
            cpp_db.functions[proxy_name] = requalify_if_needed(
                cpp_db.functions[proxy_name]
            )
            return cpp_db.functions[proxy_name]
        all_methods = {
            make_fqn(
                name=method_value.name,
                namespace=method_value.namespace,
                from_class=method_value.from_class,
            ): method_value
            for class_value in cpp_db.classes.values()
            for method_value in class_value.methods.values()
        }
        if proxy_name in all_methods:
            method_value = all_methods[proxy_name]
            class_fqn = make_fqn(
                name=method_value.from_class,
                namespace=method_value.namespace,
            )
            cpp_db.classes[class_fqn].methods[method_value.name] = requalify_if_needed(
                method_value
            )
            return cpp_db.classes[class_fqn].methods[method_value.name]

    for function_name, function_value in functions.items():
        if function_value.flags.proxy:
            if isinstance(function_value, FunctionOverloadModel):
                functions[function_name] = FunctionModel(
                    name=function_value.name,
                    namespace=function_value.namespace,
                    definition=function_value.definition,
                    parameters=[],
                    from_class=function_value.from_class,
                )
                function_value = functions[function_name]
            patch = find_and_requalify_if_needed(
                function_value.flags.proxy, function_value
            )
            patch.definition = function_value.definition
            patch.parameters = function_value.parameters
            patch.return_type = function_value.return_type
            patch.location = function_value.location
            patch.replacement = parse_definition(function_value.definition)[1]


def discard_placeholders(cpp_db):
    for class_value in cpp_db.classes.values():
        class_value.methods = {
            method_name: method
            for method_name, method in class_value.methods.items()
            if not isinstance(method, FunctionPlaceholderModel)
        }
    cpp_db.functions = {
        function_name: function
        for function_name, function in cpp_db.functions.items()
        if not isinstance(function, FunctionPlaceholderModel)
    }


def inject_ref_in_function_parameters(cpp_db: CppDatabase):
    """Function that fills the 'ref' attribute in ParameterModel
    This is used for detecting function with abstract classes passed by reference in the parameters
    (unsupported by sol)
    """

    def find_ref_from_type(typename: str):
        return cpp_db.classes.get(strip_qualifiers_from_type(typename), None)

    def fill_parameters_refs_for_function(function: FunctionUniformModel):
        if isinstance(function, FunctionModel):
            for parameter in function.parameters:
                parameter.ref = find_ref_from_type(parameter.type)
        elif isinstance(function, FunctionOverloadModel):
            for overload in function.overloads:
                for parameter in overload.parameters:
                    parameter.ref = find_ref_from_type(parameter.type)
        else:
            raise NotImplementedError()

    for function in cpp_db.functions.values():
        fill_parameters_refs_for_function(function)

    for class_value in cpp_db.classes.values():
        for method in class_value.methods.values():
            fill_parameters_refs_for_function(method)
        for constructor in class_value.constructors:
            fill_parameters_refs_for_function(constructor)


# See: https://github.com/ThePhD/sol2/issues/1259
def patch_const_ref_return_type(cpp_db: CppDatabase):
    all_functions = [function_value for function_value in cpp_db.functions.values()] + [
        method_value
        for class_value in cpp_db.classes.values()
        for method_value in class_value.methods.values()
    ]
    all_functions_overloads = [
        function_value
        for function_value in all_functions
        if isinstance(function_value, FunctionOverloadModel)
    ]
    all_functions = [
        function_value
        for function_value in all_functions
        if not isinstance(function_value, FunctionOverloadModel)
    ]
    all_functions += [
        overload
        for function_value in all_functions_overloads
        for overload in function_value.overloads
    ]

    for function_value in all_functions:
        parsed_ret_type = parse_cpp_type(function_value.return_type)
        if parsed_ret_type.qualifiers.is_const_ref():
            if (
                parsed_ret_type.type in cpp_db.classes
                and MetaTag.NonCopyable.value
                in cpp_db.classes[parsed_ret_type.type].flags.meta
            ):
                arg_list = [
                    f"{param.type} {param.name}" for param in function_value.parameters
                ]
                arg_names = [param.name for param in function_value.parameters]
                if function_value.from_class:
                    class_name = "::".join(
                        (
                            [
                                elem
                                for elem in function_value.namespace.split("::")
                                if elem
                            ]
                            + [function_value.from_class]
                        )
                    )
                    arg_list.insert(0, f"{class_name}* self")
                    function_value.flags.bind_code = (
                        f"[]({', '.join(arg_list)})"
                        f"{{ return &self->{function_value.name}({', '.join(arg_names)}); }}"
                    )
                else:
                    function_value.flags.bind_code = (
                        f"[]({', '.join(arg_list)})"
                        f"{{ return &{function_value.name}({', '.join(arg_names)}); }}"
                    )


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
def generate_bindings(cpp_db: CppDatabase, write_files: bool = True):
    global GENERATE_BINDINGS
    GENERATE_BINDINGS = write_files
    log.info("===== Generating bindings for ÖbEngine ====")
    discard_placeholders(cpp_db)
    inject_ref_in_function_parameters(cpp_db)
    patch_const_ref_return_type(cpp_db)
    generate_class_template_specialisations(cpp_db)
    apply_inherit_hook(cpp_db.classes)
    namespaces = group_bindings_by_namespace(cpp_db)
    generated_objects = {}
    for namespace_name, namespace in namespaces.items():
        copy_parent_bindings(cpp_db, namespace.classes)
        copy_parent_bases(cpp_db, namespace.classes)
        flag_abstract_classes(cpp_db, namespace.classes)
        apply_proxies(cpp_db, namespace.functions)
        generation_results = generate_bindings_for_namespace(
            cpp_db, namespace_name, namespace
        )
        generated_objects[namespace_name] = {
            "objects": generation_results[0],
            "header": generation_results[1],
            "source": generation_results[2],
        }
    if GENERATE_BINDINGS:
        for location, source_namespaces in SOURCE_DIRECTORIES_BY_OUTPUT.items():
            source_generated_objects = {
                namespace: generated_object
                for namespace, generated_object in generated_objects.items()
                if any(
                    namespace.startswith(source_namespace)
                    for source_namespace in source_namespaces
                )
            }
            source_path = LOCATIONS[location]["sources"]
            with open(
                os.path.join(OUTPUT_DIRECTORY, f"{source_path}/index.cpp"),
                "w",
            ) as bindings_index:
                bindings_index.write(
                    generated_bindings_index(location, source_generated_objects)
                )
            FILES_TO_FORMAT.append(f"{source_path}/index.cpp")
            if GENERATE_BINDINGS:
                clang_format_files(FILES_TO_FORMAT)
    return generated_objects
