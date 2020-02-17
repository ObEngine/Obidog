import argparse
import json
import os
import tempfile

import requests

from obidog.databases import CppDatabase, LuaDatabase
from obidog.bindings.generator import generate_bindings
from obidog.generators.cpp_lua_mixer import (
    mix_cpp_lua_doc, transform_all_cpp_types_to_lua_types)
from obidog.generators.doc_class_generator import generate
from obidog.logger import log
from obidog.parsers.bindings_parser import parse_all_lua_bindings
from obidog.parsers.cpp_parser import parse_doxygen_files
from obidog.wrappers.doxygen_wrapper import build_doxygen_documentation
from obidog.wrappers.git_wrapper import check_git_directory


def main():
    parser = argparse.ArgumentParser()
    # Starting Obidog
    log.info("ÖbEngine Lua Documentation Generator starting...")

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

    parser.add_argument("mode", help="Resource you want to generate", choices=["documentation", "bindings"])
    args = parser.parse_args()

    if args.mode == "documentation":
        # Processing all Lua bindings
        parse_all_lua_bindings(
            [
                os.path.join(path_to_obengine, "src", "Core", "Bindings"),
                os.path.join(path_to_obengine, "src", "Dev", "Bindings")
            ],
            lua_db
        )

        # TODO: Inject lambdas to class methods when the path is the same (method patching)

        # Merging informations from both databases
        mix_cpp_lua_doc(cpp_db, lua_db)

        # Transforming all CPP non-native types (returns / parameters) into Lua types
        transform_all_cpp_types_to_lua_types(lua_db)

        # TODO: Handle heritage
        # TODO: Inject templated return type using template specialisation in bindings

        # Generating static documentation
        generate(cwd, cpp_db.classes["obe::Animation::Animation"])
        print("Output folder", cwd)
    elif args.mode == "bindings":
        generate_bindings(cpp_db)

if __name__ == "__main__":
    main()
