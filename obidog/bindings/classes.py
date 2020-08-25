import copy
import os
from typing import List, Union, Dict

import obidog.bindings.flavours.sol3 as flavour
from obidog.bindings.functions import (
    FUNCTION_CAST_TEMPLATE,
    create_all_default_overloads,
    get_real_function_name,
)
from obidog.bindings.template import generate_template_specialization
from obidog.bindings.utils import fetch_table, make_shorthand, strip_include
from obidog.config import SOURCE_DIRECTORIES
from obidog.logger import log
from obidog.models.classes import ClassModel
from obidog.models.functions import (
    FunctionModel,
    FunctionOverloadModel,
    FunctionPatchModel,
)
from obidog.utils.string_utils import format_name

METHOD_CAST_TEMPLATE = (
    "static_cast<{return_type} ({class_name}::*)"
    "({parameters}) {qualifiers}>({method_address})"
)

METHOD_WITH_DEFAULT_VALUES_LAMBDA_WRAPPER = "[]({parameters}) -> {return_type} {{ return self->{method_call}({parameters_names}); }}"
METHOD_WITH_DEFAULT_VALUES_LAMBDA_WRAPPER_AND_PROXY = (
    "[]({parameters}) -> {return_type} {{ return {method_call}({parameters_names}); }}"
)


def generate_constructors_definitions(constructors: List[FunctionModel]):
    """This method generates all possible combinations for all constructors of a class
    If a function has 2 mandatory parameters and 3 default ones, it will generate 4 constructor
    definitions
    """
    constructors_definitions = []
    for constructor in constructors:
        constructor_definitions = []
        static_part_index = 0
        for parameter in constructor.parameters:
            if parameter.default:
                break
            static_part_index += 1
        static_part = [
            parameter.type for parameter in constructor.parameters[0:static_part_index]
        ]
        constructor_definitions.append(static_part)
        for i in range(static_part_index, len(constructor.parameters)):
            constructor_definitions.append(
                static_part
                + [
                    parameter.type
                    for parameter in constructor.parameters[static_part_index : i + 1]
                ]
            )
        constructors_definitions.append(constructor_definitions)
    return constructors_definitions


def cast_method(full_name: str, function: FunctionModel):
    if function.qualifiers.static:
        return FUNCTION_CAST_TEMPLATE.format(
            return_type=function.return_type,
            parameters=", ".join([parameter.type for parameter in function.parameters]),
            qualifiers=" ".join(
                [
                    "const" if function.qualifiers.const else "",
                    "volatile" if function.qualifiers.volatile else "",
                ]
            ),
            function_address=f"&{full_name}::{function.name}",
        )
    else:
        return METHOD_CAST_TEMPLATE.format(
            return_type=function.return_type,
            class_name=full_name,
            parameters=", ".join([parameter.type for parameter in function.parameters]),
            qualifiers=" ".join(
                [
                    "const" if function.qualifiers.const else "",
                    "volatile" if function.qualifiers.volatile else "",
                ]
            ),
            method_address=f"&{full_name}::{function.name}",
        )


def generate_method_bindings(
    full_name: str,
    method_name: str,
    method: Union[FunctionModel, FunctionOverloadModel, FunctionPatchModel],
    force_cast: bool = False,
):
    if isinstance(method, (FunctionModel, FunctionPatchModel)):
        if force_cast:
            return cast_method(full_name, method)
        else:
            address = f"&{full_name}::{method_name}"
            if hasattr(method, "replacement"):
                address = f"&{method.replacement}"
            binding = flavour.METHOD.format(address=address)
            if method.flags.as_property:
                return flavour.PROPERTY.format(address=binding)
            else:
                definitions = create_all_default_overloads(method)
                if len(definitions) > 1:
                    overloads = []
                    for definition in definitions:
                        if hasattr(method, "replacement"):
                            current_overload = METHOD_WITH_DEFAULT_VALUES_LAMBDA_WRAPPER_AND_PROXY.format(
                                parameters=",".join(
                                    [parameter.definition for parameter in definition]
                                ),
                                return_type=method.return_type,
                                method_call=method.replacement,
                                parameters_names=",".join(
                                    parameter.name for parameter in definition
                                ),
                            )
                        else:
                            current_overload = METHOD_WITH_DEFAULT_VALUES_LAMBDA_WRAPPER.format(
                                parameters=",".join(
                                    [f"{full_name}* self"]
                                    + [parameter.definition for parameter in definition]
                                ),
                                return_type=method.return_type,
                                method_call=method_name,
                                parameters_names=",".join(
                                    parameter.name for parameter in definition
                                ),
                            )
                        overloads.append(current_overload)
                    return flavour.FUNCTION_OVERLOAD.format(
                        overloads=",".join(overloads)
                    )
                else:
                    return binding
    elif isinstance(method, FunctionOverloadModel):
        casts = [cast_method(full_name, overload) for overload in method.overloads]
        return flavour.FUNCTION_OVERLOAD.format(overloads=", ".join(casts))


def generate_methods_bindings(
    body: List[str], full_name: str, lua_name: str, methods: Dict[str, FunctionModel]
):
    for method in methods.values():
        if isinstance(method, FunctionModel) and method.template:
            if method.flags.template_hints:
                for bind_name, template_hint in method.flags.template_hints.items():
                    if len(template_hint) > 1:
                        raise NotImplementedError()
                    else:
                        specialized_method = generate_template_specialization(
                            method, bind_name, template_hint[0]
                        )
                        body.append(f'bind{lua_name}["{bind_name}"] = ')
                        body.append(
                            generate_method_bindings(
                                full_name, bind_name, specialized_method, True
                            )
                        )
                        body.append(";")

            else:
                print(
                    f"[WARNING] Template hints not implemented for {full_name} -> {method.name}"
                )
        else:
            method_name = method.name
            bind_name = method.flags.bind_to or method_name
            if bind_name in flavour.TRANSLATION_TABLE:
                bind_name = flavour.TRANSLATION_TABLE[method_name]
                if bind_name is None:
                    continue
            else:
                bind_name = f'"{bind_name}"'
            body.append(f"bind{lua_name}[{bind_name}] = ")
            body.append(
                generate_method_bindings(
                    full_name, method_name, method, method.force_cast
                )
            )
            body.append(";")


def generate_class_bindings(class_value: ClassModel):
    full_name = "::".join([class_value.namespace, class_value.name])
    namespace, lua_name = full_name.split("::")[-2::]
    class_value.lua_name = ".".join(full_name.split("::"))

    constructors_signatures_str = ""
    if not class_value.abstract:
        constructors_signatures = generate_constructors_definitions(
            class_value.constructors
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
        constructors_signatures_str = (
            f", {flavour.CALL_CONSTRUCTOR}, " + constructors_signatures_str
        )
    # LATER: Register base class functions for sol3 on derived for optimization
    body = []
    generate_methods_bindings(
        body, full_name, lua_name, class_value.methods,
    )
    for attribute in class_value.attributes.values():
        if attribute.flags.nobind:
            continue
        attribute_name = attribute.name
        if attribute.type.endswith("&"):
            attribute_bind = flavour.PROPERTY_REF.format(
                class_name=full_name,
                attribute_name=attribute_name,
                property_type=attribute.type,
            )
        else:
            if attribute.qualifiers.static:
                attribute_bind = flavour.STATIC_ATTRIB.format(
                    name=f"{full_name}::{attribute_name}"
                )
            else:
                attribute_bind = f"&{full_name}::{attribute_name}"
        body.append(f'bind{lua_name}["{attribute_name}"] = {attribute_bind};')

    class_definition = constructors_signatures_str
    if class_value.bases:
        class_definition += ", " + flavour.BASE_CLASSES.format(
            bases=", ".join(class_value.bases)
        )
    namespace_access = fetch_table("::".join(full_name.split("::")[:-1])) + "\n"
    class_body = flavour.CLASS_BODY.format(
        cpp_class=f"{class_value.namespace}::{class_value.name}",
        lua_short_name=lua_name,
        namespace=namespace,
        class_definition=class_definition,
        body="\n".join(body),
        helpers="\n".join(
            [
                flavour.SCRIPT_FILE.format(source=source)
                for source in class_value.flags.helpers
            ]
        ),
    )
    # TODO: Add shorthand
    shorthand = ""
    if class_value.flags.bind_to:
        shorthand = make_shorthand(full_name, class_value.flags.bind_to)
    return namespace_access + class_body


def generate_classes_bindings(classes):
    objects = []
    includes = []
    bindings_functions = []
    for class_name, class_value in classes.items():
        if class_value.flags.nobind:
            continue
        log.info(f"  Generating bindings for class {class_name}")
        real_class_name = class_name.split("::")[-1]
        real_class_name = format_name(real_class_name)
        objects.append(f"Class{real_class_name}")
        class_path = strip_include(class_value.location)
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
        if "_fs" in binding_function:
            includes.append("#include <System/Path.hpp>")
        bindings_functions.append(binding_function)
    return {
        "includes": includes,
        "objects": objects,
        "bindings_functions": bindings_functions,
    }


def copy_parent_bases_for_one_class(cpp_db, class_value):
    inheritance_set = []
    for base in class_value.bases:
        if any(base.startswith(f"{src['namespace']}::") for src in SOURCE_DIRECTORIES):
            inheritance_set.append(base)
        base_name = base.split("<")[0]
        if base_name in cpp_db.classes:
            parent_bases = copy_parent_bases_for_one_class(
                cpp_db, cpp_db.classes[base_name]
            )
            inheritance_set += parent_bases
    return inheritance_set


def copy_parent_bases(cpp_db, classes):
    for class_value in classes.values():
        class_value.bases = list(
            dict.fromkeys(copy_parent_bases_for_one_class(cpp_db, class_value))
        )


def copy_parent_bindings(cpp_db, classes):
    for class_value in classes.values():
        if class_value.flags.copy_parent_items:
            for base in class_value.bases:
                non_template_name = base.split("<")[0]
                base_value = cpp_db.classes[non_template_name]
                base_methods = copy.deepcopy(base_value.methods)
                base_methods.update(class_value.methods)
                class_value.methods = base_methods
