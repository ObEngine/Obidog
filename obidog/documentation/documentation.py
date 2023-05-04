import os
from typing import Union

from bs4 import BeautifulSoup
from mako.template import Template
from mako.lookup import TemplateLookup
from mako import exceptions

from obidog.bindings.generator import generate_bindings, group_bindings_by_namespace
from obidog.converters.lua.types import convert_all_types
from obidog.converters.lua.urls import fill_element_urls
from obidog.databases import CppDatabase
from obidog.documentation.config import WEBSITE_URL, DOC_PATH
from obidog.documentation.search import generate_search_db
from obidog.logger import log
from obidog.models.classes import ClassModel
from obidog.models.namespace import NamespaceModel
from obidog.parsers.doxygen_index_parser import parse_doxygen_index
from obidog.wrappers.git_wrapper import get_current_branch

DB_FILENAME = "search.json"
CURRENT_VERSION = "0.5"  # TODO: Fetch version from ObEngine repo


def document_item(item: Union[ClassModel, NamespaceModel]):
    if isinstance(item, ClassModel):
        directory = os.path.join("export", "docs", *item.namespace.split("::"))
    elif isinstance(item, NamespaceModel):
        directory = os.path.join("export", "docs", *item.path.split("::"))
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


def generate_documentation(cpp_db: CppDatabase, path_to_doc: str):
    doxygen_index = parse_doxygen_index(
        os.path.join(path_to_doc, "docbuild", "xml", "index.xml")
    )
    log.info("Preparing database")
    bindings_results = generate_bindings(
        cpp_db, False
    )  # TODO: Don't forget to put this to false !

    log.info("Converting all types")
    convert_all_types(cpp_db)

    all_elements = (
        [
            item
            for item_type in cpp_db.__dict__.keys()
            for item in getattr(cpp_db, item_type).values()
            if not item.flags.nobind
        ]
        + [
            method
            for class_value in cpp_db.classes.values()
            for method in class_value.methods.values()
            if not method.flags.nobind
        ]
        + [
            attribute
            for class_value in cpp_db.classes.values()
            for attribute in class_value.attributes.values()
            if not attribute.flags.nobind
        ]
    )
    log.info("Retrieving urls for all elements")
    for element in all_elements:
        fill_element_urls(
            element,
            doxygen_index=doxygen_index,
            bindings_results=bindings_results,
            branch=get_current_branch(),
        )

    # Injecting root namespace for main index generation
    if not "" in cpp_db.namespaces:
        cpp_db.namespaces[""] = NamespaceModel(
            name="", path="", namespace="", description=""
        )
    log.info("Grouping namespace")
    namespaces = group_bindings_by_namespace(cpp_db)
    log.info("Generate namespaces documentation")
    for namespace_value in namespaces.values():
        if not namespace_value.flags.nobind:
            document_item(namespace_value)

    log.info("Generate classes documentation")
    for class_value in cpp_db.classes.values():
        if "<" in class_value.name:
            continue  # TODO: handle better templated elements
        if not class_value.flags.nobind:
            document_item(class_value)

    """log.info("Generate full database")
    with open(
        os.path.join("export", "db.json"), "w", encoding="utf-8"
    ) as db_export:
        json.dump(
            cpp_db.__dict__,
            db_export,
            indent=4,
            ensure_ascii=False,
            cls=DefaultEncoder,
        )
    """

    log.info("Generate search database")
    generate_search_db(cpp_db)
