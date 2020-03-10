import os

import obidog.bindings.flavours.sol3 as flavour
from obidog.bindings.utils import strip_include
from obidog.bindings.functions import FUNCTION_CAST_TEMPLATE
from obidog.utils.string_utils import clean_capitalize
from obidog.logger import log

METHOD_CAST_TEMPLATE = (
    "static_cast<{return_type} ({class_name}::*)"
    "({parameters}) {qualifiers}>({method_address})"
)


def generate_constructors_definitions(constructors):
    """This method generates all possible combinations for all constructors of a class
    If a function has 2 mandatory parameters and 3 default ones, it will generate 4 constructor
    definitions
    """
    constructors_definitions = []
    for constructor in constructors:
        constructor_definitions = []
        static_part_index = 0
        for parameter in constructor["parameters"]:
            if "default" in parameter:
                break
            static_part_index += 1
        static_part = [
            parameter["type"]
            for parameter in constructor["parameters"][0:static_part_index]
        ]
        constructor_definitions.append(static_part)
        for i in range(static_part_index, len(constructor["parameters"])):
            constructor_definitions.append(
                static_part
                + [
                    parameter["type"]
                    for parameter in constructor["parameters"][
                        static_part_index : i + 1
                    ]
                ]
            )
        constructors_definitions.append(constructor_definitions)
    return constructors_definitions


def generate_method_bindings(body, full_name, lua_name, methods, fields_names):
    for method in methods.values():
        method_name = method["name"]
        bind_name = method_name
        if bind_name in flavour.TRANSLATION_TABLE:
            bind_name = flavour.TRANSLATION_TABLE[method_name]
            if bind_name is None:
                continue
        else:
            bind_name = f'"{bind_name}"'
        if method["__type__"] == fields_names["simple"]:
            method_bind = flavour.METHOD.format(address=f"&{full_name}::{method_name}")
            body.append(f"bind{lua_name}[{bind_name}] = {method_bind};")
        elif method["__type__"] == fields_names["overload"]:
            casts = [
                METHOD_CAST_TEMPLATE.format(
                    return_type=overload["return_type"],
                    class_name=full_name,
                    parameters=", ".join(
                        [parameter["type"] for parameter in overload["parameters"]]
                    ),
                    qualifiers=" ".join(overload["qualifiers"]),
                    method_address=f"&{full_name}::{overload['name']}",
                ) if not overload["static"] else
                FUNCTION_CAST_TEMPLATE.format(
                    return_type=overload["return_type"],
                    parameters=", ".join(
                        [parameter["type"] for parameter in overload["parameters"]]
                    ),
                    qualifiers=" ".join(overload["qualifiers"]),
                    function_address=f"&{full_name}::{overload['name']}",
                )
                for overload in method["overloads"]
            ]
            body.append(
                f"bind{lua_name}[{bind_name}] = "
                + flavour.FUNCTION_OVERLOAD.format(overloads=", ".join(casts))
                + ";"
            )


def generate_class_bindings(class_value):
    full_name = class_value["name"]
    namespace, lua_name = full_name.split("::")[-2::]

    constructors_signatures = generate_constructors_definitions(
        class_value["constructors"]
    )
    if len(constructors_signatures) > 0:
        constructors_signatures_str = ", ".join(
            [
                f"{full_name}({', '.join(ctor)})"
                for constructor_signatures in constructors_signatures
                for ctor in constructor_signatures
            ]
        )
        constructors_signatures_str = flavour.CONSTRUCTORS.format(
            constructors=constructors_signatures_str
        )
    else:
        constructors_signatures_str = flavour.DEFAULT_CONSTRUCTOR
    # LATER: Register base class functions for sol3 on derived for optimization
    body = []
    generate_method_bindings(
        body,
        full_name,
        lua_name,
        class_value["methods"],
        {"simple": "method", "overload": "method_overload"},
    )
    generate_method_bindings(
        body,
        full_name,
        lua_name,
        class_value["static_methods"],
        {"simple": "static_method", "overload": "static_method_overload"},
    )
    for attribute in class_value["attributes"].values():
        attribute_name = attribute["name"]
        attribute_bind = flavour.PROPERTY.format(
            address=f"&{full_name}::{attribute_name}"
        )
        body.append(f'bind{lua_name}["{attribute_name}"] = {attribute_bind};')

    class_definition = constructors_signatures_str
    if class_value["bases"]:
        class_definition += ", " + flavour.BASE_CLASSES.format(
            bases=", ".join(class_value["bases"])
        )
    namespace_access = "".join(
        f'["{path_elem}"]' for path_elem in full_name.split("::")[:-1]
    )
    return flavour.CLASS_BODY.format(
        cpp_class=class_value["name"],
        lua_short_name=lua_name,
        namespace=namespace,
        namespace_path=namespace_access,
        class_definition=class_definition,
        body="\n".join(body),
        helpers="",
    )


def generate_classes_bindings(classes):
    objects = []
    includes = []
    bindings_functions = []
    for class_name, class_value in classes.items():
        log.info(f"  Generating bindings for class {class_name}")
        real_class_name = class_name.split("::")[-1]
        objects.append(f"Class{real_class_name}")
        class_path = strip_include(class_value["location"])
        class_path = class_path.replace(os.path.sep, "/")
        class_path = f"#include <{class_path}>"
        includes.append(class_path)

        state_view = flavour.STATE_VIEW
        binding_function_signature = (
            f"void LoadClass{real_class_name}({state_view} state)"
        )
        binding_function = (
            f"{binding_function_signature}\n{{\n"
            f"{generate_class_bindings(class_value)}\n}}"
        )
        bindings_functions.append(binding_function)
    return {
        "includes": includes,
        "objects": objects,
        "bindings_functions": bindings_functions,
    }
