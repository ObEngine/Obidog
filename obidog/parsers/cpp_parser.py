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
    namespaces_files = []
    classes_files = []
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
                classes_files.append(class_filepath)

            elif any(
                f.startswith(f"namespace{item['namespace']}")
                for item in SOURCE_DIRECTORIES
            ):
                namespace_filepath = os.path.join(currentDir, f)
                namespaces_files.append(namespace_filepath)
            else:
                log.warning(f"Ignoring file {f}")

    for namespace_filepath in namespaces_files:
        log.debug(f"  Parsing namespace {namespace_filepath}")
        parse_namespace_from_xml(namespace_filepath, cpp_db, doxygen_index)

    for class_filepath in classes_files:
        log.debug(f"  Parsing class {class_filepath}")
        tree = etree.parse(class_filepath)
        class_xml = tree.xpath("/doxygen/compounddef")[0]
        if class_xml.attrib.get("prot") == "private":
            continue  # ignore private classes
        class_model = parse_class_from_xml(class_xml, doxygen_index)
        if class_model.namespace in cpp_db.namespaces:
            if cpp_db.namespaces[class_model.namespace].flags.nobind:
                continue  # ignore classes from nobind namespaces
        class_fqn = make_fqn(name=class_model.name, namespace=class_model.namespace)
        cpp_db.classes[class_fqn] = class_model
        # Inner elements
        parse_enums_from_xml(
            class_fqn,
            class_xml,
            cpp_db,
        )
