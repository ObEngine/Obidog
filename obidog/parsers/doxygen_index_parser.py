from lxml import etree

from obidog.parsers.utils.xml_utils import get_content


def _get_element_identifier(element):
    return get_content(element.xpath("name")[0]).strip()


def parse_namespace(namespace, ignore_namespace=False):
    result = {}
    if not ignore_namespace:
        namespace_name = _get_element_identifier(namespace)
        refid = namespace.attrib["refid"]
        result[refid] = {
            "kind": "namespace",
            "name": namespace_name.split("::")[-1],
            "full_name": namespace_name,
            "refid": refid,
        }
    namespace_prefix = ""
    if not ignore_namespace:
        namespace_prefix = f"{namespace_name}::"

    for variable in namespace.xpath("member[@kind='variable']"):
        variable_name = _get_element_identifier(variable)
        refid = variable.attrib["refid"]
        result[refid] = {
            "kind": "variable",
            "name": variable_name,
            "full_name": f"{namespace_prefix}{variable_name}",
            "refid": refid,
        }

    for enum in namespace.xpath("member[@kind='enum']"):
        enum_name = _get_element_identifier(enum)
        refid = enum.attrib["refid"]
        result[refid] = {
            "kind": "enum",
            "name": enum_name,
            "full_name": f"{namespace_prefix}{enum_name}",
            "refid": refid,
        }

    for typedef in namespace.xpath("member[@kind='typedef']"):
        typedef_name = _get_element_identifier(typedef)
        refid = typedef.attrib["refid"]
        result[refid] = {
            "kind": "typedef",
            "name": typedef_name,
            "full_name": f"{namespace_prefix}{typedef_name}",
            "refid": refid,
        }

    for function in namespace.xpath("member[@kind='function']"):
        function_name = _get_element_identifier(function)
        refid = function.attrib["refid"]
        result[refid] = {
            "kind": "function",
            "name": function_name,
            "full_name": f"{namespace_prefix}{function_name}",
            "refid": refid,
        }

    for define in namespace.xpath("member[@kind='define']"):
        define_name = _get_element_identifier(define)
        refid = define.attrib["refid"]
        result[refid] = {
            "kind": "define",
            "name": define_name,
            "full_name": define_name,
            "refid": refid,
        }

    return result


def parse_class(class_value):
    result = {}
    class_name = _get_element_identifier(class_value)
    refid = class_value.attrib["refid"]
    result[refid] = {
        "kind": "class",
        "name": class_name.split("::")[-1],
        "full_name": class_name,
        "refid": refid,
    }

    for method in class_value.xpath("member[@kind='function']"):
        method_name = _get_element_identifier(method)
        refid = method.attrib["refid"]
        result[refid] = {
            "kind": "method",
            "name": method_name,
            "full_name": f"{class_name}::{method_name}",
            "refid": refid,
        }

    for attribute in class_value.xpath("member[@kind='variable']"):
        attribute_name = _get_element_identifier(attribute)
        refid = attribute.attrib["refid"]
        result[refid] = {
            "kind": "attribute",
            "name": attribute_name,
            "full_name": f"{class_name}::{attribute_name}",
            "refid": refid,
        }

    for inner_typedef in class_value.xpath("member[@kind='typedef']"):
        typedef_name = _get_element_identifier(inner_typedef)
        refid = inner_typedef.attrib["refid"]
        result[refid] = {
            "kind": "typedef",
            "name": typedef_name,
            "full_name": f"{class_name}::{typedef_name}",
            "refid": refid,
        }

    for inner_enum in class_value.xpath("member[@kind='enum']"):
        enum_name = _get_element_identifier(inner_enum)
        refid = inner_enum.attrib["refid"]
        result[refid] = {
            "kind": "enum",
            "name": enum_name,
            "full_name": f"{class_name}::{enum_name}",
            "refid": refid,
        }

    for inner_class in class_value.xpath("member[@kind='class']"):
        raise NotImplementedError()

    return result


def parse_doxygen_index(xml_path):
    tree = etree.parse(xml_path)

    index = tree.xpath("/doxygenindex")[0]
    classes = index.xpath("compound[@kind='class']")
    classes += index.xpath("compound[@kind='struct']")
    namespaces = index.xpath("compound[@kind='namespace']")
    non_namespaces_elements = index.xpath("compound[@kind='file']")

    index_db = {}
    for class_value in classes:
        index_db |= parse_class(class_value)

    for namespace in namespaces:
        index_db |= parse_namespace(namespace)

    for file_index in non_namespaces_elements:
        index_db |= parse_namespace(file_index, ignore_namespace=True)

    return index_db
