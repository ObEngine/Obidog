from collections import defaultdict
from obidog.databases import CppDatabase
from obidog.bindings.flavours import sol3 as flavour
from obidog.bindings.utils import strip_include
from obidog.bindings.classes import generate_classes_bindings
from obidog.bindings.enums import generate_enums_bindings
from obidog.bindings.functions import generate_functions_bindings
from obidog.bindings.globals import generate_globals_bindings
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
        f"void Load{object_name}({state_view} state);" for object_name in objects
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
        all_includes = set(
            includes for data in datasets for includes in data["includes"]
        )
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
    class_bindings = generate_classes_bindings(namespace.classes)
    enum_bindings = generate_enums_bindings(name, namespace.enums)
    functions_bindings = generate_functions_bindings(namespace.functions)
    globals_bindings = generate_globals_bindings(name, namespace.globals)

    bindings_header = os.path.join(base_path, f"{name.split('::')[-1]}.hpp").replace(
        os.path.sep, "/"
    )

    generated_objects = (
        class_bindings["objects"]
        + enum_bindings["objects"]
        + functions_bindings["objects"]
        + globals_bindings["objects"]
    )

    make_bindings_header(
        bindings_header,
        name,
        generated_objects
    )
    src_out = os.path.join("output", "src", base_path, f"{name.split('::')[-1]}.cpp")
    make_bindings_sources(
        name,
        src_out,
        bindings_header,
        enum_bindings,
        class_bindings,
        functions_bindings,
        globals_bindings
    )
    return generated_objects

# LATER: Generate bindings shorthands
def generated_bindings_index(generated_objects):
    print("Generating Bindings Index...")
    body = [
        f"#include <{flavour.INCLUDE_FILE}>",
        "namespace obe::Bindings {",
        f"void IndexAllBindings({flavour.STATE_VIEW} state)\n{{"
    ]
    for namespace_name, objects in generated_objects.items():
        ns_split = namespace_name.split("::")
        namespace_path = "".join(f"[\"{namespace_part}\"]" for namespace_part in ns_split[:-1])
        namespace_full_path = "".join(f"[\"{namespace_part}\"]" for namespace_part in ns_split)
        namespace_last_name = ns_split[-1]
        body.append(f"BindTree{namespace_path}.add(\"{namespace_last_name}\", InitTreeNodeAsTable(\"{namespace_last_name}\"));")
        body.append(f"BindTree{namespace_full_path}")
        for generated_object in objects:
            body.append(
                f".add(\"{generated_object}\", &{namespace_name}::Bindings::{generated_object})"
            )
        body.append(";\n")
    body.append("}\n}")
    return "\n".join(body)



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
def generate_bindings(cpp_db):
    log.info("===== Generating bindings for ÖbEngine ====")
    namespaces = group_bindings_by_namespace(cpp_db)
    generated_objects = {}
    for namespace_name, namespace in namespaces.items():
        generated_objects[namespace_name] = generate_bindings_for_namespace(namespace_name, namespace)
    with open("output/include/Bindings/BindingsIndex.hpp", "w") as bindings_index_inc:
        bindings_index_inc.write("#pragma once\n\n")
        # LATER: Make it flavour independant
        bindings_index_inc.write("namespace sol { class state_view; }\n")
        bindings_index_inc.write("namespace obe::Bindings {\n")
        bindings_index_inc.write(f"void IndexAllBindings({flavour.STATE_VIEW} state);\n")
        bindings_index_inc.write("}")
    with open("output/src/Bindings/BindingsIndex.cpp", "w") as bindings_index:
        bindings_index.write(generated_bindings_index(generated_objects))
    print("STOP")
