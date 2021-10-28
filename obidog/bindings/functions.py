from dataclasses import dataclass
from typing import Dict, List, Union

import obidog.bindings.flavours.sol3 as flavour
from obidog.bindings.functions_v2 import create_function_bindings
from obidog.bindings.template import generate_template_specialization
from obidog.bindings.utils import fetch_table, get_include_file
from obidog.databases import CppDatabase
from obidog.logger import log
from obidog.models.functions import FunctionModel, FunctionOverloadModel, ParameterModel
from obidog.utils.cpp_utils import make_fqn
from obidog.utils.string_utils import clean_capitalize, format_name

FUNCTION_CAST_TEMPLATE = (
    "static_cast<{return_type} (*)" "({parameters}) {qualifiers}>({function_address})"
)

FUNCTION_WITH_DEFAULT_VALUES_LAMBDA_WRAPPER = "[]({parameters}) -> {return_type} {{ return {function_call}({parameters_names}); }}"


def normalize_cpp_type(cpp_type):
    stype = cpp_type.split()
    if "const" in stype:
        stype.remove("const")
    if "volatile" in stype:
        stype.remove("volatile")
    if "&" in stype:
        stype.remove("&")
    if "*" in stype:
        stype.remove("*")
    if len(stype) > 1:
        # LATER: Improve this
        raise NotImplementedError()
    return stype[0].split("::")[-1]


OPERATOR_TABLE = {
    # LATER: Handle commented cases
    # "++": ["pre_increment", "post_increment"],
    # "--": ["pre_decrement", "post_decrement"],
    # "+": ["unary_plus", "add"],
    # "-": ["unary_minus", "subtract"],
    # "*": ["indirect", "multiply"],
    "++": "increment",
    "--": "decrement",
    "+": "add",
    "-": "subtract",
    "*": "multiply",
    "/": "divide",
    "!": "negate",
    "~": "complement",
    # "&": "address_of",
    "%": "modulus",
    "==": "equal",
    "!=": "not_equal",
    ">": "greater",
    "<": "less",
    ">=": "greater_equal",
    "<=": "less_equal",
    "<=>": "three_way_comparison",
    "&&": "logical_and",
    "||": "logical_or",
    "&": "bitwise_and",
    "|": "bitwise_or",
    "^": "bitwise_xor",
    "<<": "left_shift",
    ">>": "right_shift",
    "+=": "add_assign",
    "-=": "subtract_assign",
    "*=": "multiply_assign",
    "/=": "divide_assign",
    "%=": "modulus_assign",
    ">>=": "right_shift_assign",
    "<<=": "left_shift_assign",
    "&=": "bitwise_and_assign",
    "|=": "bitwise_or_assign",
    "^|": "bitwise_xor_assign",
    ",": "comma",
    "->*": "indirection_structure_dereference",
    "new": "allocate",
    "delete": "deallocate",
    "new[]": "allocate_array",
    "delete[]": "deallocate_array",
}


def get_real_function_name(
    function_name, function: Union[FunctionModel, FunctionOverloadModel]
):
    if function_name.startswith("operator"):
        short_operator = function_name.split("operator")[1]
        if isinstance(OPERATOR_TABLE[short_operator], str):
            if isinstance(function, FunctionOverloadModel):
                function = function.overloads[0]
            type_before = clean_capitalize(
                normalize_cpp_type(function.parameters[0].type)
            )
            operator_name = "".join(
                clean_capitalize(name_part)
                for name_part in OPERATOR_TABLE[short_operator].split("_")
            )
            type_after = ""
            if len(function.parameters) > 1:
                type_after = clean_capitalize(
                    normalize_cpp_type(function.parameters[1].type)
                )
            return "Operator", f"{type_before}{operator_name}{type_after}"
        else:
            if isinstance(function, FunctionOverloadModel):
                function = function.overloads[0]
            raise NotImplementedError()
    return "Function", function_name


PRIMITIVE_TYPES = [
    "int",
    "bool",
    "float",
    "double",
    "unsigned int",
    "size_t",
    "std::size_t",
]

FUNCTION_PROXY_TEMPLATE = """
[]({function_parameters_signature})
{{
    {function_name}({function_parameters_forward});
}}
"""


def fix_parameter_for_signature(parameter: ParameterModel):
    if (
        parameter.type.strip().endswith("&")
        and parameter.ref
        and parameter.ref.abstract
    ):
        return f"{parameter.type.removesuffix('&')}* {parameter.name}"
    elif parameter.type.endswith("&&"):
        return f"{parameter.type.removesuffix('&&')} {parameter.name}"
    elif (
        parameter.type.endswith("&") and parameter.type.rstrip(" &") in PRIMITIVE_TYPES
    ):
        return f"{parameter.type.rstrip(' &')} {parameter.name}"
    else:
        return f"{parameter.type} {parameter.name}"


def fix_parameter_for_usage(parameter: ParameterModel):
    if (
        parameter.type.strip().endswith("&")
        and parameter.ref
        and parameter.ref.abstract
    ):
        return f"*{parameter.name}"
    elif parameter.type.endswith("&&"):
        return f"std::move({parameter.name})"
    else:
        return parameter.name


def create_proxy_function(function: FunctionModel) -> str:
    function_parameters_signature = [
        fix_parameter_for_signature(parameter) for parameter in function.parameters
    ]
    function_parameters_forward = [
        fix_parameter_for_usage(parameter) for parameter in function.parameters
    ]
    return FUNCTION_PROXY_TEMPLATE.format(
        function_name=function.name,
        function_parameters_signature=",".join(function_parameters_signature),
        function_parameters_forward=",".join(function_parameters_forward),
    )


def does_requires_proxy_function(function: FunctionModel) -> bool:
    # An abstract parameter passed by reference
    if any(
        parameter.type.strip().endswith("&")
        and parameter.ref
        and parameter.ref.abstract
        for parameter in function.parameters
    ):
        return True
    # Parameter which is move-only
    elif any(parameter.type.endswith("&&") for parameter in function.parameters):
        return True
    # A primitive type is passed by reference
    if any(
        parameter.type.endswith("&") and parameter.type.rstrip(" &") in PRIMITIVE_TYPES
        for parameter in function.parameters
    ):
        return True
    return False


@dataclass
class MaybeDefaultParameter:
    definition: str
    name: str


@dataclass
class FunctionWithDefaultParameter:
    parameters: List[MaybeDefaultParameter]


"""def create_all_default_overloads(function: FunctionModel) -> List[DefaultOverloadModel]:
    function_definitions = []
    static_part_index = 0
    for parameter in function.parameters:
        if parameter.default:
            break
        static_part_index += 1
    static_part = [
        DefaultOverloadModel(f"{parameter.type} {parameter.name}", parameter.name)
        for parameter in function.parameters[0:static_part_index]
    ]
    function_definitions.append(static_part)
    for i in range(static_part_index, len(function.parameters)):
        function_definitions.append(
            static_part
            + [
                DefaultOverloadModel(
                    f"{parameter.type} {parameter.name}", parameter.name
                )
                for parameter in function.parameters[static_part_index : i + 1]
            ]
        )
    return function_definitions"""


"""def generate_function_default_value_wrapper(
    function_name: str, return_type: str, overload: DefaultOverloadModel
):
    return FUNCTION_WITH_DEFAULT_VALUES_LAMBDA_WRAPPER.format(
        parameters=",".join(parameter.definition for parameter in overload),
        return_type=return_type,
        function_call=function_name,
        parameters_names=",".join(parameter.name for parameter in overload),
    )"""


def generate_function_definitions(function_name: str, function: FunctionModel):
    """This function generates all possible combinations of a function with default parameters
    If a function has 2 mandatory parameters and 3 default ones, it will generate 4 function
    wrappers
    """
    function_definitions = create_all_default_overloads(function)

    overloads = []
    for function_definition in function_definitions:
        overloads.append(
            generate_function_default_value_wrapper(
                function_name, function.return_type, function_definition
            )
        )
    return overloads


def get_overload_static_cast(function_name: str, function_value: FunctionModel):
    return FUNCTION_CAST_TEMPLATE.format(
        return_type=function_value.return_type,
        parameters=",".join(parameter.type for parameter in function_value.parameters),
        qualifiers=" ".join(
            [
                "const" if function_value.qualifiers.const else "",
                "volatile" if function_value.qualifiers.volatile else "",
            ]
        ),
        function_address=function_name,
    )


def generate_function_bindings(
    function_name: str, function_value: Union[FunctionModel, FunctionOverloadModel]
):
    namespace_splitted = function_name.split("::")[:-1]
    function_ptr = function_name
    if isinstance(function_value, FunctionModel) and function_value.template:
        if function_value.flags.template_hints:
            full_body = ""
            for (
                bind_name,
                template_hints,
            ) in function_value.flags.template_hints.items():
                new_name = bind_name
                if len(function_name.split("::")) > 1:
                    new_name = (
                        "::".join(function_name.split("::")[:-1]) + "::" + bind_name
                    )
                if len(template_hints) == 1:
                    new_func = generate_template_specialization(
                        function_value, template_hints[0]
                    )
                    full_body += generate_function_bindings(new_name, new_func)
                else:
                    overloads = [
                        generate_template_specialization(function_value, template_hint)
                        for template_hint in template_hints
                    ]
                    funcs = FunctionOverloadModel(
                        name=new_name,
                        namespace=function_value.namespace,
                        overloads=overloads,
                    )
                    full_body += generate_function_bindings(new_name, funcs)
            return full_body
        else:
            print(f"[WARNING] No template hints found for function {function_name}")
            return ""
    if isinstance(function_value, FunctionOverloadModel):
        all_overloads = []
        for function_overload in function_value.overloads:
            if any(parameter.default for parameter in function_overload.parameters):
                all_overloads += generate_function_definitions(
                    function_name, function_value
                )
            else:
                if does_requires_proxy_function(function_overload):
                    all_overloads += [create_proxy_function(function_overload)]
                else:
                    all_overloads += [
                        get_overload_static_cast(function_name, function_overload)
                    ]
        if all_overloads:
            function_ptr = flavour.FUNCTION_OVERLOAD.format(
                overloads=",".join(all_overloads)
            )
    elif does_requires_proxy_function(function_value):
        function_ptr = create_proxy_function(function_value)
    elif any(parameter.default for parameter in function_value.parameters):
        all_overloads = create_all_default_overloads(function_value)
        all_overloads = [
            generate_function_default_value_wrapper(
                function_name, function_value.return_type, default_overload
            )
            for default_overload in all_overloads
        ]
        function_ptr = flavour.FUNCTION_OVERLOAD.format(
            overloads=",".join(all_overloads)
        )
    elif function_value.flags.bind_code:
        function_ptr = function_value.flags.bind_code

    binding_body = (
        fetch_table("::".join(namespace_splitted))
        + "\n"
        + flavour.FUNCTION_BODY.format(
            namespace=namespace_splitted[-1],
            function_name=function_value.name,
            function_ptr=function_ptr,
        )
    )
    return f"{binding_body}"


# LATER: Catch operator function and assign them to correct classes metafunctions
def generate_functions_bindings(
    cpp_db: CppDatabase,
    functions: Dict[str, Union[FunctionModel, FunctionOverloadModel]],
):
    objects = []
    includes = []
    bindings_functions = []
    for function_name, function_value in functions.items():
        log.info(f"  Generating bindings for function {function_name}")
        func_type, short_name = get_real_function_name(
            function_name.split("::")[-1], function_value
        )
        real_function_name = format_name(short_name)
        if isinstance(function_value, FunctionOverloadModel):
            identifier = (
                f"{function_value.overloads[0].namespace}::{function_value.name}"
            )
        else:
            identifier = f"{function_value.namespace}::{function_value.name}"

        if isinstance(function_value, FunctionOverloadModel):
            for overload in function_value.overloads:
                includes.append(get_include_file(overload))
        else:
            includes.append(get_include_file(function_value))

        # Do not bind proxy functions but still append related includes
        if function_value.flags.proxy:
            continue

        objects.append(
            {
                "bindings": f"{func_type}{real_function_name}",
                "identifier": identifier,
                "load_priority": function_value.flags.load_priority,
            }
        )

        state_view = flavour.STATE_VIEW
        binding_function_signature = (
            f"void LoadFunction{real_function_name}({state_view} state)"
        )

        namespace_split = function_name.split("::")[:-1]
        store_in, fetch_instruction = fetch_table("::".join(namespace_split))
        binding_function = (
            f"{binding_function_signature}\n{{\n"
            f"{fetch_instruction}"
            f"{create_function_bindings(cpp_db, store_in, function_value)}}}"
        )
        bindings_functions.append(binding_function)
    return {
        "includes": includes,
        "objects": objects,
        "bindings_functions": bindings_functions,
    }
