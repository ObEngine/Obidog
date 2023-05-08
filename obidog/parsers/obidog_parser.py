from copy import copy
from typing import Dict, List, Optional
from itertools import product

from lxml import etree

from obidog.models.flags import ObidogFlagsModel, ObidogHook, ObidogHookTrigger
from obidog.parsers.utils.doxygen_utils import doxygen_id_to_cpp_id
from obidog.utils.string_utils import replace_delimiters

TEMPLATE_HINTS_VARIABLES = {
    "lists": [
        "std::vector<int>",
        "std::vector<bool>",
        "std::vector<std::string>",
        "std::vector<double>",
    ],
    "maps": [
        "std::map<int, int>",
        "std::map<int, bool>",
        "std::map<int, std::string>",
        "std::map<int, double>",
        "std::map<bool, bool>",
        "std::map<bool, int>",
        "std::map<bool, std::string>",
        "std::map<bool, double>",
        "std::map<std::string, int>" "std::map<std::string, bool>",
        "std::map<std::string, std::string>",
        "std::map<std::string, double>",
        "std::map<double, int>" "std::map<double, bool>",
        "std::map<double, std::string>",
        "std::map<double, double>",
    ],
    "primitives": [
        "int",
        "double",
        "std::string",
        "bool",
    ],
    "numerics": ["int", "double"],
    "integers": [
        "uint8_t",
        "uint16_t",
        "uint32_t",
        "uint64_t",
        "int8_t",
        "int16_t",
        "int32_t",
        "int64_t",
    ],
    "signed_integers": [
        "int8_t",
        "int16_t",
        "int32_t",
        "int64_t",
    ],
    "unsigned_integers": ["uint8_t", "uint16_t", "uint32_t", "uint64_t"],
}


def inject_template_variables(template_combination):
    associations = {}
    for template_association in template_combination:
        template_name = template_association.split("=")[0].strip()
        associate_type = template_association.split("=")[1].strip()
        if associate_type.startswith("$"):
            if associate_type[1::] in TEMPLATE_HINTS_VARIABLES:
                associations[template_name] = TEMPLATE_HINTS_VARIABLES[
                    associate_type[1::]
                ]
            else:
                raise RuntimeError(f"Unknown template_hint variable {associate_type}")
    if not associations:
        return [template_combination]
    else:
        generated_combinations = []
        variable_combinations = [x for x in product(*associations.values())]
        for variable_combination in variable_combinations:
            current_combination = []
            for comb in template_combination:
                template_name = comb.split("=")[0].strip()
                variable_index = list(associations.keys()).index(template_name)
                if template_name in associations:
                    current_combination.append(
                        f"{template_name}={variable_combination[variable_index]}"
                    )
                else:
                    current_combination.append(comb)
            generated_combinations.append(current_combination)
        return generated_combinations


def find_obidog_flag(tree, flag_name, amount=None) -> List[str]:
    search_for = f"obidog.{flag_name}"
    flags = [
        elem.attrib["url"][len(search_for) : :]
        for elem in tree.xpath(f"*/ulink[starts-with(@url, '{search_for}')]")
    ]
    flags = [flag[1::] if flag.startswith(":") else flag for flag in flags]
    if amount:
        if len(flags) > amount:
            raise RuntimeError(
                f"Obidog flag {flag_name} found "
                f"{len(flags)} times but is needed {amount} times"
            )
    return flags


FLAG_SURROGATES: Dict[str, ObidogFlagsModel] = {}


# Simple flag parsers
def parse_obidog_boolean_flag(flag_name: str):
    def parse_obidog_flag(tree) -> bool:
        return bool(find_obidog_flag(tree, flag_name, 1))

    return parse_obidog_flag


def parse_obidog_single_value_flag(flag_name: str, transformer=lambda x: x):
    def parse_obidog_flag(tree) -> Optional[str]:
        values = find_obidog_flag(tree, flag_name, 1)
        if values:
            return transformer(values[0].strip())
        return None

    return parse_obidog_flag


def parse_obidog_many_values_flag(
    flag_name: str, transformer=lambda x: x, set_transformer=lambda x: list(x)
):
    def parse_obidog_flag(tree) -> Optional[str]:
        values = find_obidog_flag(tree, flag_name)
        if values:
            return set_transformer(transformer(value.strip()) for value in values)
        return None

    return parse_obidog_flag


# Custom flag parsers
def parse_obidog_flag_template_hint(tree):
    template_hints = find_obidog_flag(tree, "template_hint")
    if template_hints:
        thints = {}
        for template_hint in template_hints:
            bind_name, template_combination = template_hint.split(",")
            bind_name = bind_name.strip()
            template_combination = template_combination.strip().split(";")
            if bind_name not in thints:
                thints[bind_name] = []
            template_combinations = inject_template_variables(template_combination)
            for template_combination in template_combinations:
                thints[bind_name].append(
                    {
                        template_association.split("=")[0]
                        .strip(): template_association.split("=")[1]
                        .strip()
                        for template_association in template_combination
                    }
                )
        return thints
    return None


def parse_obidog_flag_rename_parameters(tree):
    def parse_rename_parameters_instruction(instruction):
        from_parameter, to_parameter = instruction.split(",")
        from_parameter, to_parameter = from_parameter.strip(), to_parameter.strip()
        return from_parameter, to_parameter

    return [
        parse_rename_parameters_instruction(instruction)
        for instruction in find_obidog_flag(tree, "paramrename")
    ]


def parse_obidog_flag_hooks(tree):
    def parse_hook_instruction(instruction):
        hook_trigger_parameter, hook_code_parameter = instruction.split(",")
        hook_trigger_parameter, hook_code_parameter = (
            hook_trigger_parameter.strip(),
            hook_code_parameter.strip(),
        )
        return ObidogHook(
            trigger=ObidogHookTrigger(hook_trigger_parameter),
            code=replace_delimiters(hook_code_parameter, "%", "{", "}"),
        )

    return [
        parse_hook_instruction(instruction)
        for instruction in find_obidog_flag(tree, "hook")
    ]


# All flags
OBIDOG_FLAGS_PARSERS = {
    "helpers": parse_obidog_many_values_flag("helper"),
    "template_hints": parse_obidog_flag_template_hint,
    "merge_template_specialisations_as": parse_obidog_single_value_flag(
        "mergetemplatespecialisations"
    ),
    "nobind": parse_obidog_boolean_flag("nobind"),
    "additional_includes": parse_obidog_many_values_flag(
        "additional_include",
        transformer=lambda additional_include: f"#include <{additional_include}>",
    ),
    "as_property": parse_obidog_boolean_flag("as_property"),
    "copy_parent_items": parse_obidog_boolean_flag("copy_parent_items"),
    "proxy": parse_obidog_single_value_flag("proxy"),
    "noconstructor": parse_obidog_boolean_flag("noconstructor"),
    "load_priority": parse_obidog_single_value_flag("loadpriority", transformer=int),
    "rename": parse_obidog_single_value_flag("rename"),
    "rename_parameters": parse_obidog_flag_rename_parameters,
    "meta": parse_obidog_many_values_flag("meta", set_transformer=set),
    "hooks": parse_obidog_flag_hooks,
}


def parse_element_obidog_flags(tree):
    flags = ObidogFlagsModel()

    for flag_name, flag_parser in OBIDOG_FLAGS_PARSERS.items():
        flag_value = flag_parser(tree)
        if flag_value:
            setattr(flags, flag_name, flag_value)

    # flag_surrogate (must be kept last)
    flag_surrogate = find_obidog_flag(tree, "flagsurrogate", 1)
    if flag_surrogate:
        flag_surrogate_target = flag_surrogate[0]
        flags_copy = flags.copy()
        if flag_surrogate_target not in FLAG_SURROGATES:
            FLAG_SURROGATES[flag_surrogate_target] = flags_copy
        else:
            FLAG_SURROGATES[flag_surrogate_target].combine(flags_copy)
        flags.nobind = True

    return flags


OBIDOG_FLAGS_DB = {}


def parse_all_obidog_flags_from_xml(flags_filepath: str):
    flags_tree = etree.parse(flags_filepath)
    elements_and_flags = flags_tree.xpath("*/detaileddescription/para/variablelist/*")
    OBIDOG_FLAGS_DB.update(
        {
            # Warning: There doesn't seem to be a problem with this yet but
            # note that some "term" have more than one ref in it
            # Usually the case is when we have a function with some referenced
            # parameters
            doxygen_id_to_cpp_id(
                element.xpath("term/ref")[0].attrib["refid"]
            ): parse_element_obidog_flags(flags)
            for element, flags in zip(elements_and_flags[::2], elements_and_flags[1::2])
        }
    )


def get_cpp_element_obidog_flags(cpp_element_id: str):
    return OBIDOG_FLAGS_DB.get(cpp_element_id, ObidogFlagsModel())


def apply_obidog_flags_surrogates(symbol_name: str, flags: ObidogFlagsModel):
    if symbol_name in FLAG_SURROGATES:
        flags.combine(FLAG_SURROGATES[symbol_name])


class ConflictsManager:
    def __init__(self):
        self.conflicts = {}

    def append(self, conflict, xml):
        if conflict not in self.conflicts:
            self.conflicts[conflict] = []
        else:
            print("Conflict detected")
        self.conflicts[conflict].append(xml)


CONFLICTS = ConflictsManager()
