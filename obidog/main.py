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
from obidog.documentation.documentation import document_item
from obidog.documentation.search import generate_search_db, DefaultEncoder


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
        log.info("Preparing database")
        generate_bindings(cpp_db, True)

        log.info("Converting all types")
        convert_all_types(cpp_db)

        all_elements = [
            item
            for item_type in cpp_db.__dict__.keys()
            for item in getattr(cpp_db, item_type).values()
        ]
        log.info("Retrieving urls for all elements")
        for element in all_elements:
            fill_element_urls(element)

        log.info("Grouping namespace")
        namespaces = group_bindings_by_namespace(cpp_db)
        log.info("Generate namespaces documentation")
        for namespace_value in namespaces.values():
            document_item(namespace_value)

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

        log.info("Generate classes documentation")
        for class_value in cpp_db.classes.values():
            document_item(class_value)

        log.info("Generate full database")
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

        log.info("Generate search database")
        generate_search_db(cpp_db)

    elif args.mode == "bindings":
        generate_bindings(cpp_db)


if __name__ == "__main__":
    main()
