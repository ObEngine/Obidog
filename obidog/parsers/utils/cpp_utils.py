import re


def _split_definition(definition: str):
    stack = [""]
    i = 0
    while i + 1 <= len(definition):
        character = definition[i]

        if character in [" ", ","]:
            if stack[-1]:
                stack.append("")
        elif character == "<":
            result, pos = _split_definition(definition[i + 1 : :])
            if not stack[-1]:
                stack[-1] = result
                stack.append("")
            else:
                stack.append(result)
                stack.append("")
            i += pos
        elif character == ">":
            if not stack[-1]:
                stack.pop()
            return stack, i + 1
        else:
            stack[-1] = stack[-1] + character
        i += 1
    if not stack[-1]:
        stack.pop()
    return stack, i


def _make_template(template_type: list):  # Shame on me
    template_type = (
        f"{template_type}".replace("[", "<")
        .replace("]", ">")
        .replace(" ", "")
        .replace(",<", "<")
        .replace(",>", "")
        .replace("'", "")[1:-1]
    )
    return re.sub(",([a-zA-Z0-9])", r", \1", template_type)


def parse_definition(definition: str):
    definition, _ = _split_definition(definition)

    stack = []
    shift = 0
    while shift < len(definition):
        if len(definition) > (shift + 1) and isinstance(definition[shift + 1], list):
            stack.append(_make_template(definition[shift : shift + 2]))
            shift += 2
        else:
            stack.append(definition[shift])
            shift += 1
    for i in range(len(stack) - 1, -1, -1):
        if stack[i].startswith("::"):
            stack[i - 1] = stack[i - 1] + stack[i]
            stack.pop(i)
    if len(stack) == 1:  # Constructors
        return "", stack[0]
    elif stack[0].endswith("::operator"):  # Cast operators
        return "", " ".join(stack)
    else:
        return " ".join(stack[0:-1]), stack[-1]


"""
res = parse_definition(
    "std::vector < std::pair < std::string, std::tuple<std::string, std::unique_ptr<int>, float> > > obe::Component::Component< T >::remove"
)
res = parse_definition(
    "std::vector < std::pair < std::string, std::tuple<std::string, std::unique_ptr<int>, float> > > obe::Component::Component::remove"
)
res = parse_definition("std::vector <std::string> obe::Component::Component::remove")
"""
