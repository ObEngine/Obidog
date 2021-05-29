import re

from obidog.logger import log
from obidog.parsers.utils.xml_utils import get_content


def merge_and_remove_duplicates(l1, l2):
    i2 = 0
    for i, x in enumerate(l1):
        if i < len(l2) and x == l2[i2]:
            i2 += 1
    return l1 + l2[i2::]


def doxygen_namespace_to_cpp_namespace(name):
    def capitalize_name(m):
        return m.group()[0] + m.group()[-1].upper()

    def capitalize_and_strip_leading_underscore(m):
        return m.group()[-1].upper()

    # Inner classes identifier ?
    name = re.sub(r"_1a", "::", name)
    name = re.sub(r"_1_1", "::", name)
    name = re.sub(r"([:0-9a-zA-Z]_[0-9a-zA-Z])", capitalize_name, name)
    name = re.sub(r"^_([0-9a-zA-Z])", capitalize_and_strip_leading_underscore, name)
    return name.replace("__", "_")


def doxygen_refid_to_cpp_name(refid):
    name = refid.attrib["refid"]
    if name.startswith("class") or name.startswith("struct"):
        name = name.removeprefix("class").removeprefix("struct")
        name = doxygen_namespace_to_cpp_namespace(name)
        name_parts = name.split("::")
        # Merging refid and text to avoid bugged names for inner classes
        short_name = refid.text.split("::")
        join_at_index = -1
        if short_name[0] in name_parts:
            join_at_index = name_parts.index(
                short_name[0], len(name_parts) - len(short_name)
            )
        return "::".join([*name_parts[:join_at_index], *short_name])
    elif name.startswith("namespace"):
        name = name.removeprefix("namespace")
        name = "_".join(name.split("_")[:-1:])
        name = doxygen_namespace_to_cpp_namespace(name)
        name = name.split("::")
        return "::".join(
            merge_and_remove_duplicates(name, get_content(refid).split("::"))
        )
    else:
        log.warning(f"Unexpected return type '{name}', defaulting as empty string")
        return ""  # raise RuntimeError(f"Unexpected Return Type '{name}'")
