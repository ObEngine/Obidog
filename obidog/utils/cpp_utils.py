import re


def make_fqn(
    name: str,
    namespace: str | None = None,
    from_class: str | None = None,
    sep: str = "::",
):
    elements = [element for element in [namespace, from_class, name] if element]
    return sep.join(elements)

def sanitize_cpp_definition(definition: str):
    # this function removes all double spaces, makes sure the cpp type is properly formatted
    sanitized_definition = re.sub(r"\s+", " ", definition)
    sanitized_definition = re.sub(r"< ", "<", sanitized_definition)
    sanitized_definition = re.sub(r" >", ">", sanitized_definition)
    sanitized_definition = re.sub(r" ,", ",", sanitized_definition)
    sanitized_definition = re.sub(r" \*", "*", sanitized_definition)
    sanitized_definition = re.sub(r" \&", "&", sanitized_definition)
    sanitized_definition = re.sub(r" \(", "(", sanitized_definition)
    sanitized_definition = re.sub(r"\( ", "(", sanitized_definition)
    sanitized_definition = re.sub(r" \)", ")", sanitized_definition)
    sanitized_definition = re.sub(r"\) ", ")", sanitized_definition)
    sanitized_definition = re.sub(r" \[", "[", sanitized_definition)
    sanitized_definition = re.sub(r"\[ ", "[", sanitized_definition)
    sanitized_definition = re.sub(r" \]", "]", sanitized_definition)
    sanitized_definition = re.sub(r"\] ", "]", sanitized_definition)
    sanitized_definition = re.sub(r" \{", "{", sanitized_definition)
    sanitized_definition = re.sub(r"\{ ", "{", sanitized_definition)
    sanitized_definition = re.sub(r" \}", "}", sanitized_definition)
    sanitized_definition = re.sub(r"\} ", "}", sanitized_definition)
    return sanitized_definition.strip()