import os

from lxml import etree
from obidog.config import SOURCE_DIRECTORIES
from obidog.logger import log
from obidog.parsers.class_parser import parse_class_from_xml
from obidog.parsers.namespace_parser import parse_namespace_from_xml
from obidog.wrappers.onlinedoc_wrapper import class_name_to_doc_link


def parse_doxygen_files(path_to_doc, cpp_db):
    log.info("Loading classes info...")
    for currentDir, _, files in os.walk(os.path.join(path_to_doc, "docbuild/xml/")):
        for f in files:
            if any(f.startswith(f"class{item['namespace']}") for item in SOURCE_DIRECTORIES):
                class_filepath = os.path.join(currentDir, f)
                log.debug(f"  Parsing class {class_filepath}")
                tree = etree.parse(class_filepath)
                class_model = parse_class_from_xml(tree.xpath("/doxygen/compounddef")[0])
                cpp_db.classes[class_model.name] = class_model
                doc_link = class_name_to_doc_link(class_model.name)
                """response = requests.get(doc_link, timeout=2)
                if response.status_code != 200:
                    print(doc_link, response.status_code)
                    raise RuntimeError(doc_link)
                else:
                    cpp_db.classes[class_name]["doc_url"] = doc_link"""
            elif any(f.startswith(f"namespace{item['namespace']}") for item in SOURCE_DIRECTORIES):
                namespace_filepath = os.path.join(currentDir, f)
                log.debug(f"  Parsing namespace {namespace_filepath}")
                parse_namespace_from_xml(namespace_filepath, cpp_db)
            else:
                log.warning(f"Ignoring file {f}")
