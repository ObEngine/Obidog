import os
import re

from obidog.config import BINDINGS_SOURCES_LOCATION, PATH_TO_OBENGINE


def CLASS_BINDING_REG(identifier, class_name, namespace):
    return (
        f"sol::usertype<{identifier}>\s*bind{class_name}"
        f"\s*=\s*{namespace}Namespace\s*.new_usertype<\s*{identifier}\s*>"
    )


def FUNCTION_BINDING_REG(function_name, namespace):
    return f'{namespace}Namespace\s*.set_function\(\s*"{function_name}"\s*,'


def METHOD_BINDING_REG(method_name, class_name):
    return f'bind{class_name}\s*\[\s*"{method_name}"\s*\]\s*='


def GLOBAL_BINDING_REG(identifier, global_name, namespace):
    return f'{namespace}Namespace\s*\[\s*"{global_name}"\s*\]\s*=\s*{identifier}\s*;'


def ENUM_BINDING_REG(identifier, namespace):
    return f"{namespace}Namespace.new_enum<{identifier}>"


def find_binding_location(location: str, element):
    # TODO: Take Location parameter into account
    full_path = os.path.join(PATH_TO_OBENGINE, BINDINGS_SOURCES_LOCATION, location)
    with open(full_path, encoding="utf-8") as bindings_source_file:
        bindings = bindings_source_file.read()
    identifier = re.escape(
        f"{element.namespace}::{element.name}" if element.namespace else element.name
    )
    last_namespace = element.namespace.split("::")[-1]
    search_result = None
    if element._type == "class":
        search_result = re.search(
            CLASS_BINDING_REG(identifier, element.name, last_namespace),
            bindings,
            re.DOTALL | re.MULTILINE,
        )
    elif element._type == "typedef":
        return 1  # Typedefs are not yet exposed to the Lua VM
    elif element._type == "namespace":
        return 1  # The whole file is the namespace, go to line 1
    elif element._type == "function":
        if hasattr(element, "from_class"):
            search_result = re.search(
                METHOD_BINDING_REG(re.escape(element.name), element.from_class),
                bindings,
                re.DOTALL | re.MULTILINE,
            )
        else:
            search_result = re.search(
                FUNCTION_BINDING_REG(re.escape(element.name), last_namespace),
                bindings,
                re.DOTALL | re.MULTILINE,
            )
    elif element._type == "global":
        search_result = re.search(
            GLOBAL_BINDING_REG(identifier, re.escape(element.name), last_namespace),
            bindings,
            re.DOTALL | re.MULTILINE,
        )
    elif element._type == "enum":
        search_result = re.search(
            ENUM_BINDING_REG(identifier, last_namespace),
            bindings,
            re.DOTALL | re.MULTILINE,
        )
    if search_result is not None:
        return bindings[0 : search_result.span()[0]].count("\n")
    else:
        return 1
