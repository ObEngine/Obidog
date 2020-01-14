from collections import defaultdict
from obeldog.databases import CppDatabase
from obeldog.generators.bindings_flavours import sol3 as flavour
import os

def group_bindings_by_namespace(cpp_db):
    group_by_namespace = defaultdict(CppDatabase)
    for item_type in ["classes", "enums", "functions", "globals", "typedefs"]:
        for item_name, item_value in getattr(cpp_db, item_type).items():
            strip_template = item_name.split("<")[0]
            last_namespace = "::".join(strip_template.split("::")[:-1:])
            getattr(group_by_namespace[last_namespace], item_type)[item_name] = item_value
    return group_by_namespace

CLASS_BINDINGS_INCLUDE_TEMPLATE = """
#pragma once

namespace {fd_sv_ns} {{ class {fd_sv_cl}; }};
namespace {ns}
{{
{fn};
}};
""".strip("\n")

CLASS_BINDINGS_SRC_TEMPLATE = """
#include <{binding_include}>
#include <{class_include}>
#include <{binding_lib}>

namemspace {ns}
{{
{fn}
{{
{fn_body}
}}
}};
""".strip("\n")

METHOD_CAST_TEMPLATE = "static_cast<{return_type} ({class_name}::*)({parameters}) {qualifiers}>({method_address})"

def generate_class_bindings(class_value):
    full_name = class_value["name"]
    namespace = class_value["name"].split("::")[0]
    lua_name = class_value["name"].split("::")[-1]
    constructors_signatures = [
        [parameter["type"] for parameter in constructor["parameters"]]
        for constructor in class_value["constructors"]
    ]
    constructors_signatures_str = ", ".join(
        [
            f"{class_value['name']}({', '.join(ctor)})"
            for ctor in constructors_signatures
        ]
    )
    body = []
    for attribute in class_value["attributes"].values():
        attribute_name = attribute["name"]
        attribute_bind = flavour.PROPERTY.format(address=f"&{full_name}::{attribute_name}")
        body.append(f"bind{lua_name}[\"{attribute_name}\"] = {attribute_bind};")
    for method in class_value["methods"].values():
        method_name = method["name"]
        bind_name = method_name
        if bind_name in flavour.TRANSLATION_TABLE:
            bind_name = flavour.TRANSLATION_TABLE[method_name]
            if bind_name is None:
                continue
        else:
            bind_name = f"\"{bind_name}\""
        if method["__type__"] == "method":
            method_bind = flavour.METHOD.format(address=f"&{full_name}::{method_name}")
            body.append(f"bind{lua_name}[{bind_name}] = {method_bind};")
        elif method["__type__"] == "method_overload":
            casts = [
                METHOD_CAST_TEMPLATE.format(
                    return_type=overload["return_type"],
                    class_name=full_name,
                    parameters=", ".join([
                        parameter["type"] for parameter in overload["parameters"]
                    ]),
                    qualifiers=", ".join(overload["qualifiers"]),
                    method_address=f"&{full_name}::{overload['name']}"
                )
                for overload in method["overloads"]
            ]
            body.append(
                f"bind{lua_name}[{bind_name}] = sol::overload({', '.join(casts)});"
            )

    return flavour.CLASS_BODY.format(
        cpp_class=class_value["name"],
        lua_short_name=lua_name,
        namespace=namespace,
        constructors=constructors_signatures_str,
        body="\n".join(body),
        helpers=""
    )

def generate_bindings_for_namespace(name, namespace):
    split_name = "/".join(name.split("::")[1::])
    base_path = f"Bindings/{split_name}"
    os.makedirs(os.path.join("output", "include", base_path), exist_ok=True)
    os.makedirs(os.path.join("output", "src", base_path), exist_ok=True)
    for class_name, class_value in namespace.classes.items():
        real_class_name = class_name.split("::")[-1]
        inc_out = os.path.join("output", "include", base_path, f"Class{real_class_name}.hpp")
        state_view = flavour.STATE_VIEW
        binding_function = f"void LoadClass{real_class_name}({state_view} state)"
        with open(inc_out, "w") as class_binding:
            class_binding.write(CLASS_BINDINGS_INCLUDE_TEMPLATE.format(
                ns=f"{name}::Bindings",
                fn=binding_function,
                fd_sv_ns="::".join(state_view.split("::")[:-1:]),
                fd_sv_cl=state_view.split("::")[-1]
            ))
        src_out = os.path.join("output", "src", base_path, f"Class{real_class_name}.hpp")
        class_path = class_value["location"]
        for strip_include in ["include/Core", "include/Dev", "include/Player"]:
            if os.path.commonprefix([strip_include, class_path]):
                class_path = os.path.relpath(class_path, strip_include)
        class_path = class_path.replace(os.path.sep, "/")
        with open(src_out, "w") as class_binding:
            state_view = flavour.STATE_VIEW
            binding_function = f"void LoadClass{real_class_name}({state_view} state)"
            class_binding.write(CLASS_BINDINGS_SRC_TEMPLATE.format(
                binding_include=f"{base_path}/Class{real_class_name}.hpp",
                binding_lib=flavour.INCLUDE_FILE,
                class_include=class_path,
                ns=f"{name}::Bindings",
                fn=binding_function,
                fn_body=generate_class_bindings(class_value)
            ))


def generate_bindings(cpp_db):
    namespaces = group_bindings_by_namespace(cpp_db)
    for namespace_name, namespace in namespaces.items():
        generate_bindings_for_namespace(namespace_name, namespace)