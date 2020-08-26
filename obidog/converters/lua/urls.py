from obidog.documentation.config import WEBSITE_URL, DOC_PATH


def get_documentation_url(element):
    if element._type == "namespace":
        element_path = "/".join(element.path.split("::"))
        return f"https://{WEBSITE_URL}/{DOC_PATH}/{element_path}"
    elif element._type == "class":
        element_path = "/".join(element.namespace.split("::"))
        return f"https://{WEBSITE_URL}/{DOC_PATH}/{element_path}/{element.name}.html"
    elif hasattr(element, "from_class"):
        element_path = "/".join(element.from_class.split("::"))
        return (
            f"https://{WEBSITE_URL}/{DOC_PATH}/{element_path}.html#doc_{element.name}"
        )
    else:
        element_path = "/".join(element.namespace.split("::"))
        return f"https://{WEBSITE_URL}/{DOC_PATH}/{element_path}#doc_{element.name}"


def fill_element_urls(element):
    if not hasattr(element, "overloads"):
        element.urls.documentation = get_documentation_url(element)
    else:
        for overload in element.overloads:
            overload.urls.documentation = get_documentation_url(overload)
