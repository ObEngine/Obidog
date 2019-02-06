import json
import logging
import os
import requests
import tempfile

from obeldog.parsers.bindings_parser import parse_all_lua_bindings
from obeldog.parsers.class_parser import parse_class_from_xml
from obeldog.wrappers.doxygen_wrapper import build_doxygen_documentation
from obeldog.wrappers.git_wrapper import clone_obengine_repo, check_obengine_repo
from obeldog.wrappers.onlinedoc_wrapper import class_name_to_doc_link
from obeldog.exceptions import InvalidObEngineGitRepositoryException

logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))

log = logging.getLogger(__name__)

def main():
    # Starting Obeldog
    log.info("ÖbEngine Lua Documentation Generator starting...")

    # Checking OBENGINE_GIT_DIRECTORY
    if "OBENGINE_GIT_DIRECTORY" in os.environ:
        path_to_obengine = os.environ["OBENGINE_GIT_DIRECTORY"]
        log.debug(f"Found existing ÖbEngine repository in {path_to_obengine}")
    else:
        log.debug("Cloning ÖbEngine repository...")
        path_to_obengine = clone_obengine_repo()
    log.debug("Checking ÖbEngine repository validity...")
    if not check_obengine_repo(path_to_obengine):
        raise InvalidObEngineGitRepositoryException(path_to_obengine)
    log.info(f"Using ÖbEngine repository in {path_to_obengine}")

    # Generating Doxygen documentation
    log.info("Building Doxygen XML documentation...")
    path_to_doc = build_doxygen_documentation(path_to_obengine)

    # Iterating over all files in Doxygen documentation
    obengine_classes = {}
    log.info("Loading classes info...")
    for currentDir, _, files in os.walk(os.path.join(path_to_doc, "docbuild/xml/")):
        for f in files:
            if f.startswith("classobe"):
                log.debug(f"  Parsing file {os.path.join(currentDir, f)}")
                class_name, class_tree = parse_class_from_xml(os.path.join(currentDir, f))
                obengine_classes[class_name] = class_tree
                doc_link = class_name_to_doc_link(class_name)
                print("=========>", class_name, doc_link)
                print("   ", json.dumps(obengine_classes[class_name], indent = 4))
                """response = requests.get(doc_link, timeout=2)
                if response.status_code != 200:
                    print(doc_link, response.status_code)
                    raise RuntimeError(doc_link)
                else:
                    obengine_classes[class_name]["doc_url"] = doc_link"""
    cwd = tempfile.mkdtemp()
    log.info(f"Working directory : {cwd}")
    print("Amount of classes", len(obengine_classes.items()))
    with open(os.path.join(cwd, "obe_classes.json"), "w") as jsonexport:
        jsonexport.write(json.dumps(obengine_classes, indent = 4))
    parse_all_lua_bindings([
        os.path.join(path_to_obengine, "src", "Core", "Bindings"),
        os.path.join(path_to_obengine, "src", "Dev", "Bindings")
    ])