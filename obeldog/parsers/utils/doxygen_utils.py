from obeldog.parsers.utils.xml_utils import get_content

def merge_and_remove_duplicates(l1, l2):
    i2 = 0
    for i, x in enumerate(l1):
        if i < len(l2) and x == l2[i2]:
            i2 += 1
    return l1 + l2[i2::]

def doxygen_namespace_to_cpp_namespace(name):
    name = name.replace("_1_1_", "::")
    name = "::".join(
        [
            x.capitalize()
            if i > 0 else x
            for i, x in
            enumerate(name.split("::"))
        ]
    )
    name = name.split("_")
    return name[0] + "".join(x.capitalize() for x in name[1::])

def doxygen_refid_to_cpp_name(refid):
    name = refid.attrib["refid"]
    if name.startswith("class") or name.startswith("struct"):
        name = name.lstrip("class").lstrip("struct")
        return doxygen_namespace_to_cpp_namespace(name)
    elif name.startswith("namespace"):
        name = name.lstrip("namespace")
        name = "_".join(name.split("_")[:-1:])
        name = doxygen_namespace_to_cpp_namespace(name)
        name = name.split("::")
        return "::".join(merge_and_remove_duplicates(
            name,
            get_content(refid).split("::")
        ))
    else:
        raise RuntimeError(f"Unexpected Return Type '{name}'")