from itertools import product

TEMPLATE_HINTS_VARIABLES = {
    "lists": [
        "std::vector<int>",
        "std::vector<bool>",
        "std::vector<std::string>",
        "std::vector<double>"
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
        "std::map<std::string, int>"
        "std::map<std::string, bool>",
        "std::map<std::string, std::string>",
        "std::map<std::string, double>",
        "std::map<double, int>"
        "std::map<double, bool>",
        "std::map<double, std::string>",
        "std::map<double, double>"
    ],
    "primitives": [
        "int", "double", "std::string", "bool",
    ],
    "numerics": [
        "int", "double"
    ]
}

def inject_template_variables(template_combination):
    associations = {}
    for template_association in template_combination:
        template_name = template_association.split("=")[0].strip()
        associate_type = template_association.split("=")[1].strip()
        if associate_type.startswith("$"):
            if associate_type[1::] in TEMPLATE_HINTS_VARIABLES:
                associations[template_name] = TEMPLATE_HINTS_VARIABLES[associate_type[1::]]
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



def find_obidog_flag(tree, flag_name, amount=None):
    search_for = f"obidog.{flag_name}"
    flags = [
        elem.attrib["url"][len(search_for)::]
        for elem in
        tree.xpath(f"detaileddescription//ulink[starts-with(@url, '{search_for}')]")
    ]
    flags = [
        flag[1::] if flag.startswith(":") else flag
        for flag in flags
    ]
    if amount:
        if len(flags) > amount:
            raise RuntimeError(
                f"Obidog flag {flag_name} found "
                f"{len(flags)} times but is needed {amount} times"
            )
    return flags

def parse_obidog_flags(tree):
    obidog_flags = {}
    bind_to = find_obidog_flag(tree, "bind", 1)
    if bind_to:
        obidog_flags["bind_to"] = bind_to[0]
    helpers = find_obidog_flag(tree, "helper")
    if helpers:
        obidog_flags["helpers"] = helpers
    private = find_obidog_flag(tree, "private", 1)
    if private and private[0] == "true":
        obidog_flags["private"] = True
    template_hints = find_obidog_flag(tree, "template_hint")
    if template_hints:
        thints = {}
        for template_hint in template_hints:
            bind_name, template_combination = template_hint.split(",")
            bind_name = bind_name.strip()
            template_combination = template_combination.strip().split(";")
            if not bind_name in thints:
                thints[bind_name] = []
            template_combinations = inject_template_variables(template_combination)
            for template_combination in template_combinations:
                thints[bind_name].append({
                    template_association.split("=")[0].strip():
                    template_association.split("=")[1].strip()
                    for template_association
                    in template_combination
                })
        obidog_flags["template_hints"] = thints
    force_abstract = find_obidog_flag(tree, "force_abstract", 1)
    if force_abstract:
        obidog_flags["abstract"] = True
    nobind = find_obidog_flag(tree, "nobind", 1)
    if nobind:
        obidog_flags["nobind"] = True
    additional_includes = find_obidog_flag(tree, "additional_include")
    if additional_includes:
        obidog_flags["additional_includes"] = [
            f"#include <{additional_include}>"
            for additional_include in additional_includes
        ]
    as_property = find_obidog_flag(tree, "as_property", 1)
    if as_property:
        obidog_flags["as_property"] = True
    return obidog_flags

class ConflictsManager:
    def __init__(self):
        self.conflicts = {}
    def append(self, conflict, xml):
        if not conflict in self.conflicts:
            self.conflicts[conflict] = []
        else:
            print("Conflict detected")
        self.conflicts[conflict].append(xml)

CONFLICTS = ConflictsManager()