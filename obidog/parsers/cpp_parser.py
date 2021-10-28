import os

from lxml import etree
from obidog.config import SOURCE_DIRECTORIES
from obidog.logger import log
from obidog.parsers.class_parser import parse_class_from_xml
from obidog.parsers.doxygen_index_parser import parse_doxygen_index
from obidog.parsers.namespace_parser import (
    parse_enums_from_xml,
    parse_namespace_from_xml,
)
from obidog.utils.cpp_utils import make_fqn


def parse_doxygen_files(path_to_doc, cpp_db):
    doxygen_index = parse_doxygen_index(
        os.path.join(path_to_doc, "docbuild", "xml", "index.xml")
    )
    log.info("Loading classes info...")
    for currentDir, _, files in os.walk(os.path.join(path_to_doc, "docbuild/xml/")):
        for f in sorted(files):
            if any(
                (
                    f.startswith(f"class{item['namespace']}")
                    or f.startswith(f"struct{item['namespace']}")
                )
                for item in SOURCE_DIRECTORIES
            ):
                class_filepath = os.path.join(currentDir, f)
                log.debug(f"  Parsing class {class_filepath}")
                tree = etree.parse(class_filepath)
                class_xml = tree.xpath("/doxygen/compounddef")[0]
                class_model = parse_class_from_xml(class_xml, doxygen_index)
                parse_enums_from_xml(
                    make_fqn(name=class_model.name, namespace=class_model.namespace),
                    class_xml,
                    cpp_db,
                )
                cpp_db.classes[
                    "::".join([class_model.namespace, class_model.name])
                ] = class_model
            elif any(
                f.startswith(f"namespace{item['namespace']}")
                for item in SOURCE_DIRECTORIES
            ):
                namespace_filepath = os.path.join(currentDir, f)
                log.debug(f"  Parsing namespace {namespace_filepath}")
                parse_namespace_from_xml(namespace_filepath, cpp_db, doxygen_index)
            else:
                log.warning(f"Ignoring file {f}")
