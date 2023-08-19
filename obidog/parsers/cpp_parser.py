import os

from lxml import etree

from obidog.config import SOURCE_DIRECTORIES
from obidog.databases import CppDatabase
from obidog.logger import log
from obidog.parsers.class_parser import parse_class_from_xml
from obidog.parsers.doxygen_index_parser import DoxygenIndex, parse_doxygen_index
from obidog.parsers.namespace_parser import (
    parse_enums_from_xml,
    parse_namespace_from_xml,
)
from obidog.parsers.obidog_parser import (
    apply_obidog_flags_surrogates,
    parse_all_obidog_flags_from_xml,
)
from obidog.utils.cpp_utils import make_fqn


def parse_doxygen_files(path_to_doc: str, cpp_db: CppDatabase) -> DoxygenIndex:
    log.info("Parsing Doxygen files...")
    doxygen_index = parse_doxygen_index(
        os.path.join(path_to_doc, "docbuild", "xml", "index.xml")
    )

    obidog_flags_filepath = os.path.join(path_to_doc, "docbuild", "xml", "obidog.xml")
    parse_all_obidog_flags_from_xml(obidog_flags_filepath)

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
                log.debug(f"Ignoring file {f}")

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

    # Keep last
    for element in [
        *cpp_db.classes.values(),
        *cpp_db.enums.values(),
        *cpp_db.functions.values(),
        *cpp_db.globals.values(),
    ]:
        if hasattr(element, "flags"):
            element_fqn = make_fqn(name=element.name, namespace=element.namespace)
            apply_obidog_flags_surrogates(element_fqn, element.flags)

    return doxygen_index
