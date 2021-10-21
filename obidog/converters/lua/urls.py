from obidog.config import OBENGINE_GIT_URL, BINDINGS_SOURCES_LOCATION
from obidog.documentation.config import DOC_PATH, DOXYGEN_PATH, WEBSITE_URL
from obidog.models.namespace import NamespaceModel
from obidog.parsers.bindings_parser import find_binding_location


def get_documentation_url(element):
    if element._type == "namespace":
        element_path = "/".join(element.path.split("::"))
        return f"https://{WEBSITE_URL}/{DOC_PATH}/{element_path}"
    elif element._type == "class":
        element_path = "/".join(element.namespace.split("::"))
        return f"https://{WEBSITE_URL}/{DOC_PATH}/{element_path}/{element.name}.html"
    elif hasattr(element, "from_class"):
        element_path = "/".join(element.namespace.split("::"))
        return f"https://{WEBSITE_URL}/{DOC_PATH}/{element_path}/{element.from_class}.html#doc_{element.name}"
    else:
        element_path = "/".join(element.namespace.split("::"))
        return f"https://{WEBSITE_URL}/{DOC_PATH}/{element_path}#doc_{element.name}"


def get_source_url(element):
    if hasattr(element, "location") and element.location.file:
        return f"{OBENGINE_GIT_URL}/blob/master/{element.location.file}#L{element.location.line}"


def get_bindings_url(bindings_results, element):
    if isinstance(element, NamespaceModel):
        namespace = element.path
    else:
        namespace = element.namespace
    if namespace in bindings_results:
        bindings_source = bindings_results[namespace]["source"]
        bindings_line = find_binding_location(bindings_source, element)
        # TODO: Take Location parameter into account
        return f"{OBENGINE_GIT_URL}/blob/master/{BINDINGS_SOURCES_LOCATION}/{bindings_source}#L{bindings_line}"
    else:
        print(f"Namespace '{namespace}' not found in bindings generation results")
        return ""


def get_doxygen_url(doxygen_index, element):
    if hasattr(element, "from_class"):
        identifier = f"{element.namespace}::{element.from_class}::{element.name}"
    elif not element.namespace:
        identifier = element.name
    else:
        identifier = f"{element.namespace}::{element.name}"
    if identifier in doxygen_index:
        doxygen_ref = doxygen_index[identifier]["refid"]
        if element._type in ["namespace", "class"]:
            return f"https://{WEBSITE_URL}/{DOXYGEN_PATH}/{doxygen_ref}.html"
        else:
            uid = doxygen_ref.split("_1")[-1]
            basepath = "_1".join(doxygen_ref.split("_1")[:-1])
            return f"https://{WEBSITE_URL}/{DOXYGEN_PATH}/{basepath}.html#{uid}"
    else:
        print(f"Failed to find identifier '{identifier}' in index_db")
        return None


def fill_element_urls(element, doxygen_index: dict = {}, bindings_results: dict = {}):
    if not hasattr(element, "overloads"):
        element.urls.documentation = get_documentation_url(element)
        if doxygen_index:
            element.urls.doxygen = get_doxygen_url(doxygen_index, element)
        element.urls.source = get_source_url(element)
        element.urls.bindings = get_bindings_url(bindings_results, element)
    else:
        for overload in element.overloads:
            fill_element_urls(
                overload,
                doxygen_index=doxygen_index,
                bindings_results=bindings_results,
            )
