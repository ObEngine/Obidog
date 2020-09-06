from lxml import etree

from obidog.parsers.utils.xml_utils import get_content


def _get_element_identifier(element):
    return get_content(element.xpath("name")[0]).strip()


def parse_doxygen_index(xml_path):
    tree = etree.parse(xml_path)

    index = tree.xpath("/doxygenindex")[0]
    classes = index.xpath("compound[@kind='class']")
    namespaces = index.xpath("compound[@kind='namespace']")

    index_db = {}
    for class_value in classes:
        class_name = _get_element_identifier(class_value)
        index_db[class_name] = {
            "kind": "class",
            "refid": class_value.attrib["refid"],
        }

        for method in class_value.xpath("member[@kind='function']"):
            method_name = _get_element_identifier(method)
            index_db[f"{class_name}::{method_name}"] = {
                "kind": "method",
                "refid": method.attrib["refid"],
            }

        for attribute in class_value.xpath("member[@kind='variable']"):
            attribute_name = _get_element_identifier(attribute)
            index_db[f"{class_name}::{attribute_name}"] = {
                "kind": "attribute",
                "refid": attribute.attrib["refid"],
            }

    for namespace in namespaces:
        namespace_name = _get_element_identifier(namespace)
        index_db[namespace_name] = {
            "kind": "namespace",
            "refid": namespace.attrib["refid"],
        }

        for variable in namespace.xpath("member[@kind='variable']"):
            variable_name = _get_element_identifier(variable)
            index_db[f"{namespace_name}::{variable_name}"] = {
                "kind": "variable",
                "refid": variable.attrib["refid"],
            }

        for enum in namespace.xpath("member[@kind='enum']"):
            enum_name = _get_element_identifier(enum)
            index_db[f"{namespace_name}::{enum_name}"] = {
                "kind": "enum",
                "refid": enum.attrib["refid"],
            }

        for typedef in namespace.xpath("member[@kind='typedef']"):
            typedef_name = _get_element_identifier(typedef)
            index_db[f"{namespace_name}::{typedef_name}"] = {
                "kind": "typedef",
                "refid": typedef.attrib["refid"],
            }

        for function in namespace.xpath("member[@kind='function']"):
            function_name = _get_element_identifier(function)
            index_db[f"{namespace_name}::{function_name}"] = {
                "kind": "function",
                "refid": function.attrib["refid"],
            }

    return index_db
