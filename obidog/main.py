import argparse
import tempfile

from obidog.bindings.generator import generate_bindings
from obidog.databases import CppDatabase
from obidog.documentation.documentation import generate_documentation
from obidog.hints.hints import generate_hints
from obidog.logger import log
from obidog.parsers.cpp_parser import parse_doxygen_files
from obidog.wrappers.doxygen_wrapper import build_doxygen_documentation
from obidog.wrappers.git_wrapper import check_git_directory


def main():
    parser = argparse.ArgumentParser()
    # Starting Obidog
    log.info("Obidog starting...")

    # Creating databases
    cpp_db = CppDatabase()

    # Checking OBENGINE_GIT_DIRECTORY
    path_to_obengine = check_git_directory()

    # Generating Doxygen documentation
    log.info("Building Doxygen XML documentation...")
    path_to_doc = build_doxygen_documentation(path_to_obengine)

    # Processing all files in Doxygen documentation
    doxygen_index = parse_doxygen_files(path_to_doc, cpp_db)

    cwd = tempfile.mkdtemp()
    log.info(f"Working directory : {cwd}")

    parser.add_argument(
        "mode",
        help="Resource you want to generate",
        choices=["documentation", "bindings", "hints"],
    )
    args = parser.parse_args()

    if args.mode == "documentation":
        generate_documentation(cpp_db, doxygen_index, path_to_doc)

    elif args.mode == "bindings":
        generate_bindings(cpp_db)

    if args.mode == "hints":
        generate_hints(cpp_db)


if __name__ == "__main__":
    main()
