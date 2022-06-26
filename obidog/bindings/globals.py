import obidog.bindings.flavours.sol3 as flavour
from obidog.utils.string_utils import format_name
from obidog.bindings.utils import fetch_table, get_include_file
from obidog.logger import log


def generate_globals_bindings(name, cpp_globals):
    includes = []
    bindings_functions = []
    objects = []
    for global_name, cpp_global in cpp_globals.items():
        if cpp_global.flags.nobind:
            continue
        export_name = format_name(cpp_global.name)
        log.info(f"  Generating bindings for global {global_name}")
        includes.append(get_include_file(cpp_global))
        objects.append(
            {
                "bindings": f"global_{export_name}",
                "identifier": f"{cpp_global.namespace}::{cpp_global.name}",
                "load_priority": cpp_global.flags.load_priority,
            }
        )
        state_view = flavour.STATE_VIEW
        binding_function_signature = (
            f"void load_global_{export_name}({state_view} state)"
        )
        _, namespace_access = fetch_table(name)
        binding_function_body = namespace_access + flavour.GLOBAL_BODY.format(
            namespace=name.split("::")[-1],
            global_name=cpp_global.name,
            global_ptr=global_name,
        )
        bindings_functions.append(
            f"{binding_function_signature}\n{{\n" f"{binding_function_body}\n}}"
        )
    return {
        "includes": includes,
        "bindings_functions": bindings_functions,
        "objects": objects,
    }
