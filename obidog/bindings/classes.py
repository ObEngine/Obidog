import os

import obidog.bindings.flavours.sol3 as flavour
from obidog.bindings.utils import strip_include

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


def generate_class_bindings(class_value):
    full_name = class_value["name"]
    namespace = class_value["name"].split("::")[0]
    lua_name = class_value["name"].split("::")[-1]

    constructors_signatures = generate_constructors_definitions(
        class_value["constructors"]
    )
    if len(constructors_signatures) > 0:
        constructors_signatures_str = ", ".join(
            [
                f"{class_value['name']}({', '.join(ctor)})"
                for constructor_signatures in constructors_signatures
                for ctor in constructor_signatures
            ]
        )
        constructors_signatures_str = flavour.CONSTRUCTORS.format(
            constructors=constructors_signatures_str
        )
    else:
        constructors_signatures_str = flavour.DEFAULT_CONSTRUCTOR
    # TODO: Register base class functions for sol3 on derived
    body = []
    for attribute in class_value["attributes"].values():
        attribute_name = attribute["name"]
        attribute_bind = flavour.PROPERTY.format(
            address=f"&{full_name}::{attribute_name}"
        )
        body.append(f'bind{lua_name}["{attribute_name}"] = {attribute_bind};')
    for method in class_value["methods"].values():
        method_name = method["name"]
        bind_name = method_name
        if bind_name in flavour.TRANSLATION_TABLE:
            bind_name = flavour.TRANSLATION_TABLE[method_name]
            if bind_name is None:
                continue
        else:
            bind_name = f'"{bind_name}"'
        if method["__type__"] == "method":
            method_bind = flavour.METHOD.format(address=f"&{full_name}::{method_name}")
            body.append(f"bind{lua_name}[{bind_name}] = {method_bind};")
        elif method["__type__"] == "method_overload":
            casts = [
                METHOD_CAST_TEMPLATE.format(
                    return_type=overload["return_type"],
                    class_name=full_name,
                    parameters=", ".join(
                        [parameter["type"] for parameter in overload["parameters"]]
                    ),
                    qualifiers=", ".join(overload["qualifiers"]),
                    method_address=f"&{full_name}::{overload['name']}",
                )
                for overload in method["overloads"]
            ]
            body.append(
                f"bind{lua_name}[{bind_name}] = sol::overload({', '.join(casts)});"
            )

    class_definition = constructors_signatures_str
    if "destructor" in class_value:
        class_definition += ", " + flavour.DESTRUCTOR.format(
            destructor="&" + class_value["destructor"]["definition"]
        )
    if class_value["bases"]:
        class_definition += ", " + flavour.BASE_CLASSES.format(
            bases=", ".join(class_value["bases"])
        )

    return flavour.CLASS_BODY.format(
        cpp_class=class_value["name"],
        lua_short_name=lua_name,
        namespace=namespace,
        class_definition=class_definition,
        body="\n".join(body),
        helpers="",
    )


def generate_classes_bindings(classes, base_path):
    objects = []
    includes = []
    bindings_functions = []
    for class_name, class_value in classes.items():
        print("  Generating bindings for class", class_name)
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
        "bindings_functions": bindings_functions
    }