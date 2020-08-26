import argparse
import json
import os
import tempfile

import requests

from obidog.converters.lua.types import convert_all_types
from obidog.converters.lua.namespace import group_bindings_by_namespace
from obidog.converters.lua.urls import fill_element_urls
from obidog.databases import CppDatabase, LuaDatabase
from obidog.bindings.generator import generate_bindings
from obidog.generators.cpp_lua_merge import (
    mix_cpp_lua_doc,
    transform_all_cpp_types_to_lua_types,
)
from obidog.generators.doc_class_generator import generate
from obidog.logger import log
from obidog.parsers.bindings_parser import parse_all_lua_bindings
from obidog.parsers.cpp_parser import parse_doxygen_files
from obidog.wrappers.doxygen_wrapper import build_doxygen_documentation
from obidog.wrappers.git_wrapper import check_git_directory
from obidog.documentation.documentation import document_class, document_namespace


class DefaultEncoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__


def main():
    parser = argparse.ArgumentParser()
    # Starting Obidog
    log.info("Obidog starting...")

    # Creating databases
    cpp_db = CppDatabase()
    lua_db = LuaDatabase()

    # Checking OBENGINE_GIT_DIRECTORY
    path_to_obengine = check_git_directory()

    # Generating Doxygen documentation
    log.info("Building Doxygen XML documentation...")
    path_to_doc = build_doxygen_documentation(path_to_obengine)

    # Processing all files in Doxygen documentation
    parse_doxygen_files(path_to_doc, cpp_db)

    cwd = tempfile.mkdtemp()
    log.info(f"Working directory : {cwd}")

    parser.add_argument(
        "mode",
        help="Resource you want to generate",
        choices=["documentation", "bindings"],
    )
    args = parser.parse_args()

    if args.mode == "documentation":
        generate_bindings(cpp_db, True)
        convert_all_types(cpp_db)

        namespaces = group_bindings_by_namespace(cpp_db)
        for namespace_value in namespaces.values():
            document_namespace(namespace_value)

        doxygen_url = "https://obengine.io/doc/cpp/classobe_1_1_collision_1_1_polygonal_collider.html#a972819e978772fbcf1ec3b25ddb124a8"
        source_url = "https://github.com/Sygmei/ObEngine/blob/master/src/Core/Collision/PolygonalCollider.cpp#L170"
        bindings_url = "https://github.com/Sygmei/ObEngine/blob/master/src/Core/Bindings/obe/Collision/Collision.cpp#L71"
        urls = (
            cpp_db.classes["obe::Collision::PolygonalCollider"]
            .methods["removeTag"]
            .urls
        )
        urls.doxygen = doxygen_url
        urls.source = source_url
        urls.bindings = bindings_url
        for class_value in cpp_db.classes.values():
            document_class(class_value)
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
        search_db = [
            item
            for item_type in cpp_db.__dict__.keys()
            for item in getattr(cpp_db, item_type).values()
        ]
        for class_value in cpp_db.classes.values():
            for method in class_value.methods.values():
                if method._type == "overload":
                    method = method.overloads[0]
                method.from_class = f"{class_value.namespace}::{class_value.name}"
                method._type = "method"
                search_db.append(method)
        for item in search_db:
            if item._type == "namespace":
                for elem in ["typedefs", "globals", "functions", "enums"]:
                    item.__dict__.pop(elem)
        for element in search_db:
            if element._type == "overload":
                element.urls = element.overloads[0].urls
                element._type = "function"
                element.namespace = element.overloads[0].namespace
        for element in search_db:
            fill_element_urls(element)
        for element in search_db:
            to_pop = []
            for attr in element.__dict__:
                if attr not in ["_type", "name", "namespace", "from_class", "urls"]:
                    to_pop.append(attr)
            for attr in to_pop:
                element.__dict__.pop(attr)
        with open(
            os.path.join("export", "search.json"), "w", encoding="utf-8"
        ) as db_export:

            json.dump(
                search_db, db_export, indent=4, ensure_ascii=False, cls=DefaultEncoder,
            )
        """# Processing all Lua bindings
        parse_all_lua_bindings(
            [
                os.path.join(path_to_obengine, "src", "Core", "Bindings"),
                os.path.join(path_to_obengine, "src", "Dev", "Bindings"),
            ],
            lua_db,
        )

        # Merging informations from both databases
        mix_cpp_lua_doc(cpp_db, lua_db)

        # Transforming all CPP non-native types (returns / parameters) into Lua types
        transform_all_cpp_types_to_lua_types(lua_db)

        # Generating static documentation
        generate(cwd, cpp_db.classes["obe::Animation::Animation"])
        log.debug("Output folder", cwd)"""
    elif args.mode == "bindings":
        generate_bindings(cpp_db)


if __name__ == "__main__":
    main()
