from obidog.models.location import LocalizableModel

import os
import obidog.bindings.flavours.sol3 as flavour
from obidog.config import SOURCE_DIRECTORIES


def strip_include(path):
    for strip_path in [src["path"] for src in SOURCE_DIRECTORIES]:
        if os.path.commonprefix([strip_path, path]):
            path = os.path.relpath(path, strip_path)
    return path


def fetch_table(full_namespace):
    namespace_splitted = full_namespace.split("::")
    return flavour.FETCH_TABLE.format(
        namespace=namespace_splitted[-1],
        namespace_path="".join(f'["{path_elem}"]' for path_elem in namespace_splitted),
    )


# TODO: Support for metatable shorthand
# TODO: Support for table / metatable deps, if a shorthand requires a table, check that it's not created elsewhere
def make_shorthand(full_name, shorthand):
    namespace_splitted = full_name.split("::")
    shorthand_splitted = shorthand.split(".")
    return flavour.SHORTHAND.format(
        namespace_path="".join(f'["{path_elem}"]' for path_elem in namespace_splitted),
        shorthand_path="".join(f'["{path_elem}"]' for path_elem in shorthand_splitted),
    )


def get_include_file(item: LocalizableModel):
    include_path = strip_include(item.location.file)
    include_path = include_path.replace(os.path.sep, "/")
    return f"#include <{include_path}>"


def strip_qualifiers_from_type(cpp_type: str):
    buffer = ""
    while buffer != cpp_type:
        buffer = cpp_type
        cpp_type = cpp_type.rstrip(" &*[]")
        cpp_type = cpp_type.removeprefix("const")
        cpp_type = cpp_type.strip()
        cpp_type = cpp_type.removeprefix("volatile")
    return cpp_type
