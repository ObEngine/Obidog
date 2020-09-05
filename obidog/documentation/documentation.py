import os
from typing import Union

from bs4 import BeautifulSoup
from mako.template import Template
from mako.lookup import TemplateLookup
from mako import exceptions

from obidog.models.classes import ClassModel
from obidog.models.namespace import NamespaceModel
from obidog.documentation.config import WEBSITE_URL, DOC_PATH

DB_FILENAME = "search.json"
CURRENT_VERSION = "0.5"  # TODO: Fetch version from ObEngine repo


def document_item(item: Union[ClassModel, NamespaceModel]):
    if isinstance(item, ClassModel):
        directory = os.path.join("export", *item.namespace.split("::"))
    elif isinstance(item, NamespaceModel):
        directory = os.path.join("export", *item.path.split("::"))
    os.makedirs(directory, exist_ok=True)
    name = f"{item.name}.html" if isinstance(item, ClassModel) else "index.html"
    with open(
        os.path.join(directory, name),
        "w",
        encoding="utf-8",
    ) as export:
        with open(
            "templates/documentation/lua_body.mako", "r", encoding="utf-8"
        ) as tpl:
            try:
                lookup = TemplateLookup(["templates/documentation"])
                html_string = Template(tpl.read(), lookup=lookup).render(
                    target=item,
                    WEBSITE_LOCATION=WEBSITE_URL,
                    DOCUMENTATION_PATH=DOC_PATH,
                    DB_LOCATION=f"{WEBSITE_URL}/{DOC_PATH}/{DB_FILENAME}",
                    CURRENT_VERSION=CURRENT_VERSION,
                )
                pretty_html = BeautifulSoup(html_string, "html.parser").prettify()
                export.write(pretty_html)
            except Exception as e:
                export.write(exceptions.html_error_template().render().decode("utf-8"))
