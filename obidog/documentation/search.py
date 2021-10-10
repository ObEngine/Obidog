from enum import Enum
import json
import os

from obidog.databases import CppDatabase


class DefaultEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Enum):
            return o.value
        return o.__dict__


def _make_search_db(cpp_db: CppDatabase):
    return [
        item
        for item_type in cpp_db.__dict__.keys()
        for item in getattr(cpp_db, item_type).values()
    ]


def _add_overloads(cpp_db: CppDatabase, search_db):
    for class_value in cpp_db.classes.values():
        for method in class_value.methods.values():
            if method._type == "overload":
                method = method.overloads[0]
            method.from_class = f"{class_value.namespace}::{class_value.name}"
            method._type = "method"
            search_db.append(method)


def _add_attributes(cpp_db: CppDatabase, search_db):
    for class_value in cpp_db.classes.values():
        for attribute in class_value.attributes.values():
            attribute.from_class = f"{class_value.namespace}::{class_value.name}"
            search_db.append(attribute)


def _strip_namespace_content(search_db):
    for item in search_db:
        if item._type == "namespace":
            for elem in ["typedefs", "globals", "functions", "enums"]:
                item.__dict__.pop(elem)


def _fix_overloads(search_db: CppDatabase):
    for element in search_db:
        if element._type == "overload":
            element.urls = element.overloads[0].urls
            element._type = "function"
            element.namespace = element.overloads[0].namespace


def _strip_unnecessary_attributes(search_db: CppDatabase):
    for element in search_db:
        to_pop = []
        element.url = element.urls.documentation
        for attr in element.__dict__:
            if attr not in ["_type", "name", "namespace", "from_class", "url"]:
                to_pop.append(attr)
        for attr in to_pop:
            element.__dict__.pop(attr)


def generate_search_db(cpp_db: CppDatabase):
    search_db = _make_search_db(cpp_db)
    _add_overloads(cpp_db, search_db)
    _add_attributes(cpp_db, search_db)
    _strip_namespace_content(search_db)
    _fix_overloads(search_db)
    _strip_unnecessary_attributes(search_db)

    with open(
        os.path.join("export", "search.json"), "w", encoding="utf-8"
    ) as db_export:

        json.dump(
            search_db,
            db_export,
            indent=4,
            ensure_ascii=False,
            cls=DefaultEncoder,
        )
