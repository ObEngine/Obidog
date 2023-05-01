from collections import defaultdict
from copy import copy
from dataclasses import dataclass
from itertools import groupby
from typing import List, Optional, Union

import obidog.bindings.flavours.sol3 as flavour
from obidog.bindings.models import BindableFunctionModel, BindingsSourceCode
from obidog.bindings.template import generate_template_specialization
from obidog.databases import CppDatabase
from obidog.logger import log
from obidog.models.flags import MetaTag
from obidog.models.functions import FunctionModel, FunctionOverloadModel, ParameterModel
from obidog.parsers.type_parser import parse_cpp_type
from obidog.utils.cpp_utils import make_fqn

REACTIVE_ATTRIBUTE_TEMPLATE = "sol::property({function_call})"

CALL_WRAPPER_TPL = (
    "[]"
    "({parameters})"
    " -> {return_type}"
    "{{"
    "return "
    "{function_call_prefix}"
    "{function_call}"
    "({parameters_names})"
    "{function_call_suffix}"
    ";"
    "}}"
)


def make_call_wrapper(
    function_value: BindableFunctionModel,
):
    all_parameters = (
        function_value.prefix_call_args
        + function_value.parameters
        + function_value.postfix_call_args
    )
    return CALL_WRAPPER_TPL.format(
        parameters=",".join(
            f"{parameter.type} {parameter.name}" for parameter in all_parameters
        ),
        return_type=function_value.return_type,
        function_call=function_value.function_call,
        parameters_names=",".join(
            parameter.name for parameter in function_value.parameters
        ),
        function_call_prefix=function_value.call_prefix or "",
        function_call_suffix=function_value.call_suffix or "",
    )


FUNCTION_CAST_TEMPLATE = (
    "static_cast<{return_type} ({function_location}*)"
    "({parameters}) {qualifiers}>(&{fqn})"
)


def make_static_cast(function_value: BindableFunctionModel):
    function_location = ""
    if function_value.from_class:
        function_location = make_fqn(
            name=function_value.from_class, namespace=function_value.namespace
        )
        function_location = f"{function_location}::"
    return FUNCTION_CAST_TEMPLATE.format(
        return_type=function_value.return_type,
        function_location=function_location,
        parameters=",".join(parameter.type for parameter in function_value.parameters),
        qualifiers=" ".join(
            [
                "const" if function_value.qualifiers.const else "",
                "volatile" if function_value.qualifiers.volatile else "",
            ]
        ),
        fqn=function_value.fqn,
    )


def create_all_default_parameter_specialisations(
    function_value: BindableFunctionModel,
) -> List[BindableFunctionModel]:
    specialisations = []
    static_part_index = 0
    for parameter in function_value.parameters:
        if parameter.default:
            break
        static_part_index += 1
    static_part = [
        ParameterModel(type=parameter.type, name=parameter.name)
        for parameter in function_value.parameters[0:static_part_index]
    ]
    specialisations.append(
        BindableFunctionModel(
            **(
                function_value.__dict__
                | {"parameters": static_part, "requires_call_wrapper": True}
            )
        )
    )
    for i in range(static_part_index, len(function_value.parameters)):
        parameter_set = static_part + [
            ParameterModel(type=parameter.type, name=parameter.name)
            for parameter in function_value.parameters[static_part_index : i + 1]
        ]
        specialisations.append(
            BindableFunctionModel(
                **(
                    function_value.__dict__
                    | {"parameters": parameter_set, "requires_call_wrapper": True}
                )
            )
        )
    return specialisations


@dataclass
class FunctionBindingGenerationOptions:
    is_overload: bool = False


def make_bindable_function_model(
    function_value: Union[FunctionModel, FunctionOverloadModel]
):
    is_method = bool(function_value.from_class)

    # Get fully qualified name
    if is_method:
        fqn = make_fqn(
            name=function_value.name,
            namespace=function_value.namespace,
            from_class=function_value.from_class,
        )
        class_fqn = make_fqn(
            name=function_value.from_class, namespace=function_value.namespace
        )

    else:
        fqn = make_fqn(
            name=function_value.name,
            namespace=function_value.namespace,
        )

    # Define function call / function call args
    function_call = fqn
    prefix_call_args = []
    if is_method and not function_value.qualifiers.static:
        if function_value.constructor:
            function_call = class_fqn
        # Proxy functions do not need to inject self (they already have it)
        elif not function_value.replacement:
            function_call = f"self->{function_value.name}"
            prefix_call_args = [
                ParameterModel(
                    name="self",
                    type=f"{class_fqn}*",
                )
            ]

    existing_attributes = function_value.__dict__

    # Detect "rename" flag
    if function_value.flags.rename:
        existing_attributes.update({"name": function_value.flags.rename})

    # Build BindableFunctionModel with additional infos
    return BindableFunctionModel(
        **existing_attributes,
        fqn=fqn,
        function_call=function_call,
        prefix_call_args=prefix_call_args,
        requires_static_cast=function_value.force_cast,
    )


def generate_function_specialisations(
    cpp_db: CppDatabase,
    function_value: Union[FunctionModel, FunctionOverloadModel],
    options: Optional[FunctionBindingGenerationOptions] = None,
) -> List[BindableFunctionModel]:
    options = options or FunctionBindingGenerationOptions()

    specialisations = []

    # Detect if function is overloaded
    if isinstance(function_value, FunctionOverloadModel):
        overload_specialisations = []
        for overload in function_value.overloads:
            overload_options = copy(options)
            overload_options.is_overload = True
            overload_specialisations += generate_function_specialisations(
                cpp_db=cpp_db, function_value=overload, options=overload_options
            )
        return overload_specialisations

    ext_function_value = make_bindable_function_model(function_value)

    discard_base_function = False

    # Detect if function is deleted
    if function_value.deleted:
        return []

    # Detect if function is replaced by a proxy
    if function_value.replacement:
        ext_function_value.fqn = function_value.replacement
        ext_function_value.function_call = function_value.replacement

    # Detect if function has default parameters
    if any(parameter.default is not None for parameter in function_value.parameters):
        discard_base_function = True
        specialisations += create_all_default_parameter_specialisations(
            ext_function_value
        )

    # Detect if function has const reference non-copyable return type
    parsed_return_type = parse_cpp_type(ext_function_value.return_type)
    if parsed_return_type.qualifiers.is_const_ref():
        if (
            parsed_return_type.type in cpp_db.classes
            and MetaTag.NonCopyable.value
            in cpp_db.classes[parsed_return_type.type].flags.meta
        ):
            parsed_return_type.qualifiers.prefix_qualifiers = ["const"]
            parsed_return_type.qualifiers.postfix_qualifiers = ["*"]
            ext_function_value.return_type = str(parsed_return_type)
            ext_function_value.requires_call_wrapper = True
            ext_function_value.call_prefix = "&"

    # Detect if function is templated and provides template hints
    if ext_function_value.template:
        discard_base_function = True
        if ext_function_value.flags.template_hints:
            for (
                bind_name,
                template_hints,
            ) in function_value.flags.template_hints.items():
                template_specialisation_base = BindableFunctionModel(
                    **(
                        ext_function_value.__dict__
                        | {"name": bind_name, "requires_static_cast": True}
                    )
                )
                for template_hint in template_hints:
                    template_specialisation_with_hints = (
                        generate_template_specialization(function_value, template_hint)
                    )
                    specialisations.append(
                        BindableFunctionModel(
                            **(
                                template_specialisation_base.__dict__
                                | template_specialisation_with_hints.__dict__
                            )
                        )
                    )
        else:
            log.warn(
                f"No template hints provided for function {ext_function_value.fqn}"
            )

    # No specialisations yet and function is overloaded, we need to static_cast it
    if not specialisations and options.is_overload:
        ext_function_value.requires_static_cast = True

    if not discard_base_function:
        specialisations.append(ext_function_value)

    return specialisations


def make_bindings_source_code(
    bindable_function: BindableFunctionModel,
) -> BindingsSourceCode:
    if bindable_function.requires_call_wrapper:
        function_call = make_call_wrapper(bindable_function)
    elif bindable_function.requires_static_cast:
        function_call = make_static_cast(bindable_function)
    else:
        function_call = f"&{bindable_function.fqn}"
    return function_call


def make_function_bind_name_string(function_value: BindableFunctionModel) -> str:
    bind_name = function_value.name
    if bind_name in flavour.OPERATOR_TRANSLATION_TABLE:
        translation = flavour.OPERATOR_TRANSLATION_TABLE[bind_name]
        if isinstance(translation, dict):
            for translation_name, translation_condition in translation.items():
                if translation_condition(function_value):
                    return translation_name
            return None
        else:
            return translation
    return f'"{bind_name}"'


def make_bind_instruction(
    store_in: str,
    bind_name: str,
    function_call: str,
    function_value: BindableFunctionModel,
) -> str:
    if function_value.from_class:
        return f"{store_in}[{bind_name}] = {function_call};"
    else:
        return f"{store_in}.set_function({bind_name}, {function_call});"


def create_function_bindings(
    cpp_db: CppDatabase,
    store_in: str,
    function_value: Union[FunctionModel, FunctionOverloadModel],
) -> List[BindingsSourceCode]:
    specialisations = generate_function_specialisations(cpp_db, function_value)

    if len(specialisations) == 1:
        single_specialisation = specialisations[0]
        function_call = make_bindings_source_code(single_specialisation)
        if function_value.flags.as_property:
            function_call = REACTIVE_ATTRIBUTE_TEMPLATE.format(
                function_call=function_call
            )
        bind_name = make_function_bind_name_string(single_specialisation)
        if bind_name is None:
            return
        return make_bind_instruction(
            store_in=store_in,
            bind_name=bind_name,
            function_call=function_call,
            function_value=single_specialisation,
        )
    else:
        bindings_by_function_name = []
        specialisations_bind_names = defaultdict(list)
        for specialisation in specialisations:
            specialisations_bind_names[
                make_function_bind_name_string(specialisation)
            ].append(specialisation)
        specialisations_bind_names = {
            key: value
            for key, value in specialisations_bind_names.items()
            if key is not None
        }
        sort_and_group_by_bind_name_criteria = (
            lambda bind_name_and_specialisation: bind_name_and_specialisation[0]
        )
        specialisations_bind_names = sorted(
            specialisations_bind_names.items(),
            key=sort_and_group_by_bind_name_criteria,
        )
        for bind_name, specialisations_by_bind_name in groupby(
            specialisations_bind_names, key=sort_and_group_by_bind_name_criteria
        ):
            # Extracting single list element [0] and value from dict tuple [1]
            specialisations_by_bind_name = list(specialisations_by_bind_name)[0][1]
            binding_source_code = [
                make_bindings_source_code(specialisation)
                for specialisation in specialisations_by_bind_name
            ]
            if len(specialisations_by_bind_name) > 1:
                function_calls = f'sol::overload({", ".join(binding_source_code)})'
            else:
                function_calls = binding_source_code[0]
            bind_instruction = make_bind_instruction(
                store_in=store_in,
                bind_name=bind_name,
                function_call=function_calls,
                function_value=specialisations_by_bind_name[0],
            )
            bindings_by_function_name.append(bind_instruction)
        return "\n".join(bindings_by_function_name)
