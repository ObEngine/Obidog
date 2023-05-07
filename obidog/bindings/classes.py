import copy
from dataclasses import dataclass
import os
from typing import List, Dict, Optional, Set

import obidog.bindings.flavours.sol3 as flavour
from obidog.bindings.functions import does_requires_proxy_function
from obidog.bindings.functions_v2 import create_function_bindings
from obidog.bindings.template import generate_template_specialization
from obidog.bindings.utils import fetch_table, make_shorthand, strip_include
from obidog.config import SOURCE_DIRECTORIES
from obidog.databases import CppDatabase
from obidog.logger import log
from obidog.models.classes import ClassModel
from obidog.models.flags import ObidogHook, ObidogHookTrigger
from obidog.models.functions import (
    FunctionModel,
    FunctionOverloadModel,
)
from obidog.parsers.type_parser import parse_cpp_type
from obidog.utils.cpp_utils import make_fqn
from obidog.utils.string_utils import format_name

METHOD_CAST_TEMPLATE = (
    "static_cast<{return_type} ({class_name}::*)"
    "({parameters}) {qualifiers}>({method_address})"
)

METHOD_WITH_DEFAULT_VALUES_LAMBDA_WRAPPER = (
    "[]({parameters}) -> {return_type} "
    "{{ return self->{method_call}({parameters_names}); }}"
)
METHOD_WITH_DEFAULT_VALUES_LAMBDA_WRAPPER_AND_PROXY = (
    "[]({parameters}) -> {return_type} {{ return {method_call}({parameters_names}); }}"
)


@dataclass
class ClassConstructors:
    signatures: List[List[str]]
    constructible: bool


def generate_hook_call(ctx: ClassModel, hook: ObidogHook) -> Optional[str]:
    if hook.trigger == ObidogHookTrigger.Bind:
        return f"{ctx.name}::{hook.call}();"


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


METHOD_PROXY_TEMPLATE = """
[]({class_type}* self, {method_parameters_signature})
{{
    self->{method_name}({method_parameters_forward});
}}
"""


def generate_templated_method_bindings(
    cpp_db: CppDatabase,
    body: List[str],
    class_name: str,
    lua_name: str,
    method: FunctionModel,
):
    if method.flags.template_hints:
        for bind_name, template_hint in method.flags.template_hints.items():
            if len(template_hint) > 1:
                raise NotImplementedError()
            else:
                specialized_method = generate_template_specialization(
                    method, template_hint[0]
                )
                specialized_method.flags.rename = bind_name
                specialized_method.force_cast = True
                store_in = f"bind_{format_name(lua_name)}"
                body.append(
                    create_function_bindings(cpp_db, store_in, specialized_method)
                )
                body.append(";")

    else:
        print(
            f"[WARNING] Template hints not implemented for {class_name} -> {method.name}"
        )


def generate_methods_bindings(
    cpp_db: CppDatabase,
    body: List[str],
    class_name: str,
    lua_name: str,
    methods: Dict[str, FunctionModel],
):
    for method in methods.values():
        if isinstance(method, FunctionModel) and method.template:
            generate_templated_method_bindings(
                cpp_db, body, class_name, lua_name, method
            )
        else:
            store_in = f"bind_{format_name(lua_name)}"
            method_bindings = create_function_bindings(cpp_db, store_in, method)
            if method_bindings:
                body.append(method_bindings)


def generate_class_bindings(cpp_db: CppDatabase, class_value: ClassModel):
    full_name = make_fqn(
        name=class_value.flags.rename or class_value.name,
        namespace=class_value.namespace,
    )
    real_name = make_fqn(name=class_value.name, namespace=class_value.namespace)
    namespace, lua_name = full_name.split("::")[-2::]

    constructors_signatures_str = ""
    if not class_value.abstract and not class_value.flags.noconstructor:
        private_constructors = any(
            internal_func.name == class_value.name
            for internal_func in class_value.private_methods.values()
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
                    f"{real_name}({', '.join(ctor)})"
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
        cpp_db,
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
        body.append(
            f'bind_{format_name(lua_name)}["{attribute_name}"] = {attribute_bind};'
        )

    class_definition = constructors_signatures_str
    if class_value.bases:
        class_definition += ", " + flavour.BASE_CLASSES.format(
            bases=", ".join(class_value.bases)
        )
    _, namespace_access = fetch_table("::".join(full_name.split("::")[:-1]))
    class_body = flavour.CLASS_BODY.format(
        cpp_class=f"{class_value.namespace}::{class_value.name}",
        lua_formatted_name=format_name(lua_name),
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
        hooks="\n".join(
            # Generate hook calls and filter out None values
            [
                hook_call
                for hook_call in [
                    hook.call
                    for hook in class_value.flags.hooks
                    if hook.trigger == ObidogHookTrigger.Bind
                ]
                if hook_call
            ]
        ),
    )
    # TODO: Add shorthand
    shorthand = ""
    if class_value.flags.rename:
        shorthand = make_shorthand(full_name, class_value.flags.rename)
    return namespace_access + class_body


def generate_classes_bindings(cpp_db: CppDatabase, classes: Dict[str, ClassModel]):
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
                "bindings": f"class_{real_class_name}",
                "identifier": f"{class_value.namespace}::{class_value.name}",
                "load_priority": class_value.flags.load_priority,
            }
        )
        class_path = strip_include(class_value.location.file)
        class_path = class_path.replace(os.path.sep, "/")
        class_path = f"#include <{class_path}>"
        includes_for_class.append(class_path)

        state_view = flavour.STATE_VIEW
        binding_function_signature = (
            f"void load_class_{real_class_name}({state_view} state)"
        )
        binding_function = (
            f"{binding_function_signature}\n{{\n"
            f"{generate_class_bindings(cpp_db, class_value)}\n}}"
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


def generate_class_template_specialisations(cpp_db: CppDatabase):
    specialisations = {}
    specialisations_merges = {}
    remove_base_templated_class_list = []
    for class_name, class_value in cpp_db.classes.items():
        # Only applies for templated classes with template hints
        if not class_value.template or not class_value.flags.template_hints:
            continue
        for (
            specialisation_name,
            specialisation_typeset,
        ) in class_value.flags.template_hints.items():
            for specialisation_types in specialisation_typeset:
                specialisation = copy.deepcopy(class_value)
                specialisation.name = (
                    f"{class_value.name}<{', '.join(specialisation_types.values())}>"
                )
                specialisation.flags.rename = specialisation_name
                constructors_and_methods: List[
                    FunctionModel
                ] = specialisation.constructors + list(specialisation.methods.values())
                for method in constructors_and_methods:
                    method.from_class = specialisation.name
                    for parameter in method.parameters:
                        parameter_type = parse_cpp_type(parameter.type)
                        # If the parameter type is one of the class template type
                        # we replace it by the specialized type hint
                        parameter_type.traverse(
                            lambda ptype: specialisation_types.get(ptype, ptype)
                        )
                        parameter.type = str(parameter_type)
                    # Adding return type (specialized class) for constructors
                    if not method.return_type:
                        method.return_type = specialisation.name
                    return_type = parse_cpp_type(method.return_type)
                    return_type.traverse(
                        lambda rtype: specialisation_types.get(rtype, rtype)
                    )
                    method.return_type = str(return_type)
                    if method.flags.merge_template_specialisations_as:
                        if (
                            not method.flags.merge_template_specialisations_as
                            in specialisations_merges
                        ):
                            specialisations_merges[
                                method.flags.merge_template_specialisations_as
                            ] = []
                        specialisations_merges[
                            method.flags.merge_template_specialisations_as
                        ].append(method)
                specialisations[
                    make_fqn(name=specialisation_name, namespace=class_value.namespace)
                ] = specialisation
        remove_base_templated_class_list.append(class_name)
    cpp_db.classes |= specialisations
    for remove_base_templated_class in remove_base_templated_class_list:
        cpp_db.classes.pop(remove_base_templated_class)
    for specialisations_merge_name, specialisations in specialisations_merges.items():
        specialisation_fqn = make_fqn(
            name=specialisations_merge_name, namespace=specialisations[0].namespace
        )
        specialisations_copy = [
            copy.deepcopy(specialisation) for specialisation in specialisations
        ]
        for specialisation in specialisations_copy:
            specialisation.flags.rename = specialisations_merge_name
        cpp_db.functions[specialisation_fqn] = FunctionOverloadModel(
            name=specialisations_merge_name,
            namespace=specialisations[0].namespace,
            overloads=specialisations_copy,
            flags=specialisations[0].flags,
            force_cast=True,
            from_class=specialisations[0].from_class,
        )


def copy_parent_bases(cpp_db: CppDatabase, classes: Dict[str, ClassModel]):
    def copy_parent_bases_for_one_class(cpp_db, class_value):
        inheritance_set = []
        for base in class_value.get_bases():
            if any(
                base.startswith(f"{src['namespace']}::") for src in SOURCE_DIRECTORIES
            ):
                inheritance_set.append(base)
            strip_template_base = base.split("<")[0]
            if strip_template_base in cpp_db.classes:
                parent_bases = copy_parent_bases_for_one_class(
                    cpp_db, cpp_db.classes[strip_template_base]
                )
                inheritance_set += parent_bases
        return inheritance_set

    for class_value in classes.values():
        class_value.bases = list(
            dict.fromkeys(copy_parent_bases_for_one_class(cpp_db, class_value))
        )


def apply_inherit_hook(classes: Dict[str, ClassModel]):
    for class_value in classes.values():
        if any(
            hook.trigger == ObidogHookTrigger.Inherit
            for hook in class_value.flags.hooks
        ):
            full_class_name = make_fqn(
                name=class_value.name,
                namespace=class_value.namespace,
            )
            child_classes = [
                child_class
                for child_class in classes.values()
                if full_class_name in child_class.get_bases(strip_template_types=True)
            ]
            for hook in class_value.flags.hooks:
                if hook.trigger == ObidogHookTrigger.Inherit:
                    for child_class in child_classes:
                        child_class_fqn = make_fqn(
                            name=child_class.name,
                            namespace=child_class.namespace,
                        )
                        child_class.flags.hooks |= {
                            ObidogHook(
                                trigger=ObidogHookTrigger.Bind,
                                call=hook.call.replace("%childclass%", child_class_fqn),
                            )
                        }


def copy_parent_bindings(cpp_db, classes: Dict[str, ClassModel]):
    for class_value in classes.values():
        if class_value.flags.copy_parent_items:
            for base in class_value.get_bases(strip_template_types=True):
                base_value = cpp_db.classes[base]
                base_methods = copy.deepcopy(base_value.methods)
                for base_method in base_methods.values():
                    base_method.from_class = class_value.name
                    base_method.namespace = class_value.namespace
                base_methods.update(class_value.methods)
                class_value.methods = base_methods


def flag_abstract_classes(cpp_db, classes):
    for class_value in classes.values():
        class_bases = class_value.get_bases(discard_template_types=True)
        if not class_value.abstract and any(
            cpp_db.classes[base].abstract for base in class_bases
        ):
            bases = [cpp_db.classes[base] for base in class_bases]
            bases = [base for base in bases if base.abstract]
            abstract_methods = [
                method
                for base in bases
                for method in [*base.private_methods.values(), *base.methods.values()]
                if isinstance(method, FunctionModel) and method.abstract
            ]
            abstract_methods_names = [method.name for method in abstract_methods]
            # TODO: Better implementation for overloads
            implemented_methods = [
                method
                for method in [
                    *class_value.private_methods.values(),
                    *class_value.methods.values(),
                ]
                if isinstance(method, FunctionModel)
                and method.name in abstract_methods_names
                and not method.abstract
            ]
            implemented_methods += [
                method.overloads[0]
                for method in [
                    *class_value.private_methods.values(),
                    *class_value.methods.values(),
                ]
                if isinstance(method, FunctionOverloadModel)
                and method.name in abstract_methods_names
                and any(not overload.abstract for overload in method.overloads)
            ]
            implemented_methods += [
                method
                for parent_class in [cpp_db.classes[base] for base in class_bases]
                for method in [
                    *parent_class.private_methods.values(),
                    *parent_class.methods.values(),
                ]
                if method.name in abstract_methods_names and not method.abstract
            ]
            if set(abstract_methods_names) - set(
                method.name for method in implemented_methods
            ):
                class_value.abstract = True
