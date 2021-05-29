import copy
from dataclasses import dataclass
import os
from typing import List, Union, Dict

import obidog.bindings.flavours.sol3 as flavour
from obidog.bindings.functions import (
    FUNCTION_CAST_TEMPLATE,
    create_all_default_overloads,
    does_requires_proxy_function,
    PRIMITIVE_TYPES,
    fix_parameter_for_signature,
    fix_parameter_for_usage,
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
    ParameterModel,
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


@dataclass
class ClassConstructors:
    signatures: List[List[str]]
    constructible: bool


def generate_constructors_definitions(constructors: List[FunctionModel]):
    """This method generates all possible combinations for all constructors of a class
    If a function has 2 mandatory parameters and 3 default ones, it will generate 4 constructor
    definitions
    """
    constructors_definitions = []
    deleted_constructors = 0
    for constructor in constructors:
        if (
            constructor.deleted
            or constructor.template
            or does_requires_proxy_function(constructor)
        ):
            deleted_constructors += 1
            continue
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
    return ClassConstructors(
        signatures=constructors_definitions,
        constructible=(deleted_constructors == 0 or len(constructors_definitions) > 0),
    )


def cast_method(class_name: str, method: FunctionModel):
    if does_requires_proxy_function(method):
        return create_proxy_method(class_name, method)
    elif method.qualifiers.static:
        return FUNCTION_CAST_TEMPLATE.format(
            return_type=method.return_type,
            parameters=", ".join([parameter.type for parameter in method.parameters]),
            qualifiers=" ".join(
                [
                    "const" if method.qualifiers.const else "",
                    "volatile" if method.qualifiers.volatile else "",
                ]
            ),
            function_address=f"&{class_name}::{method.name}",
        )
    else:
        return METHOD_CAST_TEMPLATE.format(
            return_type=method.return_type,
            class_name=class_name,
            parameters=", ".join([parameter.type for parameter in method.parameters]),
            qualifiers=" ".join(
                [
                    "const" if method.qualifiers.const else "",
                    "volatile" if method.qualifiers.volatile else "",
                ]
            ),
            method_address=f"&{class_name}::{method.name}",
        )


METHOD_PROXY_TEMPLATE = """
[]({class_type}* self, {method_parameters_signature})
{{
    self->{method_name}({method_parameters_forward});
}}
"""


def create_proxy_method(class_name: str, method: FunctionModel) -> str:
    method_parameters_signature = [
        fix_parameter_for_signature(parameter) for parameter in method.parameters
    ]
    method_parameters_forward = [
        fix_parameter_for_usage(parameter) for parameter in method.parameters
    ]
    return METHOD_PROXY_TEMPLATE.format(
        method_name=method.name,
        class_type=class_name,
        method_parameters_signature=",".join(method_parameters_signature),
        method_parameters_forward=",".join(method_parameters_forward),
    )


def generate_method_bindings(
    class_name: str,
    method_name: str,
    method: Union[FunctionModel, FunctionOverloadModel, FunctionPatchModel],
    force_cast: bool = False,
):
    if isinstance(method, (FunctionModel, FunctionPatchModel)):
        if method.deleted:
            return
        if does_requires_proxy_function(method):
            return create_proxy_method(class_name, method)
        if force_cast:
            return cast_method(class_name, method)
        else:
            address = f"&{class_name}::{method_name}"
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
                            current_overload = (
                                METHOD_WITH_DEFAULT_VALUES_LAMBDA_WRAPPER.format(
                                    parameters=",".join(
                                        [f"{class_name}* self"]
                                        + [
                                            parameter.definition
                                            for parameter in definition
                                        ]
                                    ),
                                    return_type=method.return_type,
                                    method_call=method_name,
                                    parameters_names=",".join(
                                        parameter.name for parameter in definition
                                    ),
                                )
                            )
                        overloads.append(current_overload)
                    return flavour.FUNCTION_OVERLOAD.format(
                        overloads=",".join(overloads)
                    )
                else:
                    return binding
    elif isinstance(method, FunctionOverloadModel):
        casts = [
            cast_method(class_name, overload)
            for overload in method.overloads
            if not overload.template
        ]
        if casts:
            return flavour.FUNCTION_OVERLOAD.format(overloads=", ".join(casts))


def generate_templated_method_bindings(
    body: List[str], class_name: str, lua_name: str, method: FunctionModel
):
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
                        class_name, bind_name, specialized_method, True
                    )
                )
                body.append(";")

    else:
        print(
            f"[WARNING] Template hints not implemented for {class_name} -> {method.name}"
        )


def generate_methods_bindings(
    body: List[str], class_name: str, lua_name: str, methods: Dict[str, FunctionModel]
):
    for method in methods.values():
        # TODO: Skip deleted methods
        if isinstance(method, FunctionModel) and method.template:
            generate_templated_method_bindings(body, class_name, lua_name, method)
        else:
            bind_name = method.flags.bind_to or method.name
            if bind_name in flavour.TRANSLATION_TABLE:
                bind_name = flavour.TRANSLATION_TABLE[method.name]
                if bind_name is None:
                    continue
            else:
                bind_name = f'"{bind_name}"'
            method_bindings = generate_method_bindings(
                class_name, method.name, method, method.force_cast
            )
            if method_bindings:
                body.append(f"bind{lua_name}[{bind_name}] = ")
                body.append(method_bindings)
                body.append(";")


def generate_class_bindings(class_value: ClassModel):
    full_name = "::".join([class_value.namespace, class_value.name])
    namespace, lua_name = full_name.split("::")[-2::]
    class_value.lua_name = ".".join(full_name.split("::"))

    constructors_signatures_str = ""
    if (
        not (class_value.abstract or class_value.flags.abstract)
        and not class_value.flags.noconstructor
    ):
        private_constructors = any(
            internal_func.name == class_value.name
            for internal_func in class_value.internal.values()
        )
        constructors_signatures = generate_constructors_definitions(
            class_value.constructors
        )
        constructible = (
            constructors_signatures.constructible and not private_constructors
        )
        if len(constructors_signatures.signatures) > 0:
            constructors_signatures_str = ", ".join(
                [
                    f"{full_name}({', '.join(ctor)})"
                    for constructor_signatures in constructors_signatures.signatures
                    for ctor in constructor_signatures
                ]
            )
            constructors_signatures_str = flavour.CONSTRUCTORS.format(
                constructors=constructors_signatures_str
            )
        elif constructible:
            constructors_signatures_str = flavour.DEFAULT_CONSTRUCTOR
        constructors_signatures_str = (
            (f", {flavour.CALL_CONSTRUCTOR}, " + constructors_signatures_str)
            if constructible
            else ""
        )
    # LATER: Register base class functions for sol3 on derived for optimization
    body = []
    generate_methods_bindings(
        body,
        full_name,
        lua_name,
        class_value.methods,
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
        includes_for_class = []
        if class_value.flags.nobind:
            continue
        log.info(f"  Generating bindings for class {class_name}")
        real_class_name = class_name.split("::")[-1]
        real_class_name = format_name(real_class_name)
        objects.append(
            {
                "bindings": f"Class{real_class_name}",
                "identifier": f"{class_value.namespace}::{class_value.name}",
            }
        )
        class_path = strip_include(class_value.location.file)
        class_path = class_path.replace(os.path.sep, "/")
        class_path = f"#include <{class_path}>"
        includes_for_class.append(class_path)

        state_view = flavour.STATE_VIEW
        binding_function_signature = (
            f"void LoadClass{real_class_name}({state_view} state)"
        )
        binding_function = (
            f"{binding_function_signature}\n{{\n"
            f"{generate_class_bindings(class_value)}\n}}"
        )
        if "_fs" in binding_function:
            includes_for_class.append("#include <System/Path.hpp>")
        if class_value.flags.additional_includes:
            includes_for_class += class_value.flags.additional_includes
        bindings_functions.append(binding_function)
        includes.append("\n".join(includes_for_class))
    return {
        "includes": includes,
        "objects": objects,
        "bindings_functions": bindings_functions,
    }


def copy_parent_bases(cpp_db, classes):
    def copy_parent_bases_for_one_class(cpp_db, class_value):
        inheritance_set = []
        for base in class_value.bases:
            if any(
                base.startswith(f"{src['namespace']}::") for src in SOURCE_DIRECTORIES
            ):
                inheritance_set.append(base)
            base_name = base.split("<")[0]
            if base_name in cpp_db.classes:
                parent_bases = copy_parent_bases_for_one_class(
                    cpp_db, cpp_db.classes[base_name]
                )
                inheritance_set += parent_bases
        return inheritance_set

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


def flag_abstract_classes(cpp_db, classes):
    for class_value in classes.values():
        if not class_value.abstract and any(
            cpp_db.classes[base].abstract for base in class_value.bases
        ):
            bases = [cpp_db.classes[base] for base in class_value.bases]
            bases = [base for base in bases if base.abstract]
            abstract_methods = [
                method
                for base in bases
                for method in [*base.internal.values(), *base.methods.values()]
                if isinstance(method, FunctionModel) and method.abstract
            ]
            abstract_methods_names = [method.name for method in abstract_methods]
            implemented_methods = [
                method
                for method in [
                    *class_value.internal.values(),
                    *class_value.methods.values(),
                ]
                if method.name in abstract_methods_names and not method.abstract
            ]
            implemented_methods += [
                method
                for parent_class in [cpp_db.classes[base] for base in class_value.bases]
                for method in [
                    *parent_class.internal.values(),
                    *parent_class.methods.values(),
                ]
                if method.name in abstract_methods_names and not method.abstract
            ]
            if set(abstract_methods_names) - set(
                method.name for method in implemented_methods
            ):
                class_value.abstract = True
