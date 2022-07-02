from dataclasses import dataclass, field
from typing import Dict
from lxml import etree

from obidog.parsers.utils.xml_utils import get_content


def _get_element_identifier(element):
    return get_content(element.xpath("name")[0]).strip()


@dataclass
class DoxygenElement:
    kind: str
    name: str
    fqn: str
    refid: str


@dataclass
class DoxygenIndex:
    by_refid: Dict[str, DoxygenElement] = field(default_factory=lambda: {})
    by_fqn: Dict[str, DoxygenElement] = field(default_factory=lambda: {})

    def register_element(
        self,
        *,
        kind: str,
        refid: str,
        fqn: str,
        name: str,
    ):
        element = DoxygenElement(kind=kind, name=name, fqn=fqn, refid=refid)
        self.by_refid[refid] = element
        self.by_fqn[fqn] = element

    def __or__(self, other: "DoxygenIndex"):
        return DoxygenIndex(
            by_refid=self.by_refid | other.by_refid, by_fqn=self.by_fqn | other.by_fqn
        )


def parse_namespace(namespace, ignore_namespace=False):
    result = DoxygenIndex()
    if not ignore_namespace:
        namespace_name = _get_element_identifier(namespace)
        refid = namespace.attrib["refid"]
        result.register_element(
            kind="namespace",
            refid=refid,
            fqn=namespace_name,
            name=namespace_name.split("::")[-1],
        )
    namespace_prefix = ""
    if not ignore_namespace:
        namespace_prefix = f"{namespace_name}::"

    for variable in namespace.xpath("member[@kind='variable']"):
        variable_name = _get_element_identifier(variable)
        refid = variable.attrib["refid"]
        fqn = f"{namespace_prefix}{variable_name}"
        result.register_element(
            kind="variable", refid=refid, fqn=fqn, name=variable_name
        )

    for enum in namespace.xpath("member[@kind='enum']"):
        enum_name = _get_element_identifier(enum)
        refid = enum.attrib["refid"]
        fqn = f"{namespace_prefix}{enum_name}"
        result.register_element(kind="enum", refid=refid, fqn=fqn, name=enum_name)

    for typedef in namespace.xpath("member[@kind='typedef']"):
        typedef_name = _get_element_identifier(typedef)
        refid = typedef.attrib["refid"]
        fqn = f"{namespace_prefix}{typedef_name}"
        result.register_element(kind="typedef", refid=refid, fqn=fqn, name=typedef_name)

    for function in namespace.xpath("member[@kind='function']"):
        function_name = _get_element_identifier(function)
        refid = function.attrib["refid"]
        fqn = f"{namespace_prefix}{function_name}"
        result.register_element(
            kind="function", refid=refid, fqn=fqn, name=function_name
        )

    for define in namespace.xpath("member[@kind='define']"):
        define_name = _get_element_identifier(define)
        refid = define.attrib["refid"]
        fqn = define_name
        result.register_element(kind="define", refid=refid, fqn=fqn, name=define_name)

    return result


def parse_class(class_value):
    result = DoxygenIndex()
    class_name = _get_element_identifier(class_value)
    refid = class_value.attrib["refid"]
    result.register_element(
        kind="class", refid=refid, fqn=class_name, name=class_name.split("::")[-1]
    )

    for method in class_value.xpath("member[@kind='function']"):
        method_name = _get_element_identifier(method)
        refid = method.attrib["refid"]
        fqn = f"{class_name}::{method_name}"
        result.register_element(kind="method", refid=refid, fqn=fqn, name=method_name)

    for attribute in class_value.xpath("member[@kind='variable']"):
        attribute_name = _get_element_identifier(attribute)
        refid = attribute.attrib["refid"]
        fqn = f"{class_name}::{attribute_name}"
        result.register_element(
            kind="attribute", refid=refid, fqn=fqn, name=attribute_name
        )

    for inner_typedef in class_value.xpath("member[@kind='typedef']"):
        typedef_name = _get_element_identifier(inner_typedef)
        refid = inner_typedef.attrib["refid"]
        fqn = f"{class_name}::{typedef_name}"
        result.register_element(kind="typedef", refid=refid, fqn=fqn, name=typedef_name)

    for inner_enum in class_value.xpath("member[@kind='enum']"):
        enum_name = _get_element_identifier(inner_enum)
        refid = inner_enum.attrib["refid"]
        fqn = f"{class_name}::{enum_name}"
        result.register_element(kind="enum", refid=refid, fqn=fqn, name=enum_name)

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

    index_db = DoxygenIndex()
    for class_value in classes:
        index_db |= parse_class(class_value)

    for namespace in namespaces:
        index_db |= parse_namespace(namespace)

    for file_index in non_namespaces_elements:
        index_db |= parse_namespace(file_index, ignore_namespace=True)

    return index_db
