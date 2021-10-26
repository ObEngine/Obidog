from collections import defaultdict
from copy import copy
from dataclasses import dataclass
from itertools import groupby
from typing import List, Optional, Union

from obidog.bindings.models import BindableFunctionModel, BindingsSourceCode
from obidog.bindings.template import generate_template_specialization
from obidog.logger import log
from obidog.models.functions import FunctionModel, FunctionOverloadModel, ParameterModel
from obidog.parsers.type_parser import parse_cpp_type
from obidog.utils.cpp_utils import make_fqn


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
    "({parameters}) {qualifiers}>({fqn})"
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
    is_method = hasattr(function_value, "from_class")

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
    if is_method:
        function_call = f"self->{function_value.name}"
        prefix_call_args = [
            ParameterModel(
                name="self",
                type=f"{class_fqn}*",
            )
        ]

    # Build BindableFunctionModel with additional infos
    return BindableFunctionModel(
        **function_value.__dict__,
        fqn=fqn,
        function_call=function_call,
        prefix_call_args=prefix_call_args,
    )


def prepare_function_bindings(
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
            overload_specialisations += prepare_function_bindings(
                function_value=overload, options=overload_options
            )
        return overload_specialisations

    ext_function_value = make_bindable_function_model(function_value)

    discard_base_function = False

    # Detect if function has default parameters
    if any(parameter.default is not None for parameter in function_value.parameters):
        discard_base_function = True
        specialisations += create_all_default_parameter_specialisations(
            ext_function_value
        )

    # Detect if function has const reference return type
    parsed_return_type = parse_cpp_type(ext_function_value.return_type)
    if parsed_return_type.qualifiers.is_const_ref():
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
        return make_call_wrapper(bindable_function)
    if bindable_function.requires_static_cast:
        return make_static_cast(bindable_function)
    else:
        return f"&{bindable_function.fqn}"


def create_function_bindings(
    store_in: str, function_value: Union[FunctionModel, FunctionOverloadModel]
) -> List[BindingsSourceCode]:
    specialisations = prepare_function_bindings(function_value)

    if len(specialisations) == 1:
        single_specialisation = specialisations[0]
        return (
            f'{store_in}["{single_specialisation.name}"] = '
            f"{make_bindings_source_code(single_specialisation)};"
        )
    else:
        bindings_by_function_name = []
        for function_name, specialisations_by_func_name in groupby(
            specialisations, key=lambda f: f.name
        ):
            specialisations_by_func_name = list(specialisations_by_func_name)
            binding_source_code = [
                make_bindings_source_code(specialisation)
                for specialisation in specialisations_by_func_name
            ]
            if len(specialisations_by_func_name) > 1:
                bindings_by_function_name.append(
                    f'{store_in}["{function_name}"] = '
                    f'sol::overload({", ".join(binding_source_code)});'
                )
        return "\n".join(bindings_by_function_name)
