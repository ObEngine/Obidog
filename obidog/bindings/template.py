from copy import deepcopy

from obidog.models.functions import FunctionModel


def replace_template_type(value, search, replace):
    return " ".join(elem if elem != search else replace for elem in value.split())


def generate_template_specialization(function: FunctionModel, hints):
    function = deepcopy(function)
    function.template = False
    if function.flags.template_hints:
        function.flags.template_hints = []
    for template_class_name, template_hint in hints.items():
        if template_class_name in function.return_type.split():
            function.return_type = replace_template_type(
                function.return_type, template_class_name, template_hint
            )
        for parameter in function.parameters:
            if template_class_name in parameter.type.split():
                parameter.type = replace_template_type(
                    parameter.type, template_class_name, template_hint
                )
    return function
