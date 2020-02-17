import os

from obidog.logger import log
from obidog.parsers.class_parser import parse_class_from_xml
from obidog.parsers.namespace_parser import parse_namespace_from_xml
from obidog.wrappers.onlinedoc_wrapper import class_name_to_doc_link

def parse_doxygen_files(path_to_doc, cpp_db):
    log.info("Loading classes info...")
    for currentDir, _, files in os.walk(os.path.join(path_to_doc, "docbuild/xml/")):
        for f in files:
            if f.startswith("classobe"):
                class_filepath = os.path.join(currentDir, f)
                log.debug(f"  Parsing class {class_filepath}")
                class_name, class_tree = parse_class_from_xml(class_filepath)
                cpp_db.classes[class_name] = class_tree
                doc_link = class_name_to_doc_link(class_name)
                """response = requests.get(doc_link, timeout=2)
                if response.status_code != 200:
                    print(doc_link, response.status_code)
                    raise RuntimeError(doc_link)
                else:
                    cpp_db.classes[class_name]["doc_url"] = doc_link"""
            elif f.startswith("namespaceobe"):
                namespace_filepath = os.path.join(currentDir, f)
                log.debug(f"  Parsing namespace {namespace_filepath}")
                parse_namespace_from_xml(namespace_filepath, cpp_db)
            else:
                log.warning(f"Ignoring file {f}")
