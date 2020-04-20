import os

from obidog.config import PATH_TO_OBENGINE
from obidog.exceptions import ParameterNameNotFoundInXMLException
from obidog.parsers.utils.xml_utils import (
    get_content,
    get_content_if,
    extract_xml_value,
)
from obidog.parsers.utils.doxygen_utils import doxygen_refid_to_cpp_name
from obidog.parsers.function_parser import parse_function_from_xml
from obidog.parsers.obidog_parser import parse_obidog_flags, CONFLICTS


def parse_methods(class_name, class_value):
    methods = {}
    constructors = []
    destructor = None
    if len(class_value.xpath("sectiondef[@kind='public-func']")) > 0:
        for xml_method in class_value.xpath("sectiondef[@kind='public-func']")[0]:
            method = parse_function_from_xml(xml_method, method=True)
            if method:
                if method["name"] == class_name.split("::")[-1]:
                    constructors.append(method)
                elif method["name"] == f"~{class_name.split('::')[-1]}":
                    destructor = method
                else:
                    if method["name"] in methods:
                        overload = methods[method["name"]]
                        if overload["__type__"].endswith("_overload"):
                            overload["overloads"].append(method)
                        else:
                            methods[method["name"]] = {
                                "__type__": "method_overload",
                                "name": method["name"],
                                "overloads": [overload, method],
                            }
                    else:
                        methods[method["name"]] = method
    return {"methods": methods, "constructors": constructors, "destructor": destructor}


def parse_attributes(class_value):
    attributes = {}
    for xml_attribute in class_value.xpath(
        "sectiondef[@kind='public-attrib']/memberdef[@kind='variable']"
    ):
        attribute_name = get_content(xml_attribute.find("name"))
        attributes[attribute_name] = {
            "__type__": "attribute",
            "type": get_content(xml_attribute.find("type")),
            "name": attribute_name,
            "description": get_content(xml_attribute.find("briefdescription")),
            "static": False,
            **parse_obidog_flags(xml_attribute)
        }
    for xml_attribute in class_value.xpath(
        "sectiondef[@kind='public-static-attrib']/memberdef[@kind='variable']"
    ):
        attribute_name = get_content(xml_attribute.find("name"))
        attributes[attribute_name] = {
            "__type__": "attribute",
            "type": get_content(xml_attribute.find("type")),
            "name": attribute_name,
            "description": get_content(xml_attribute.find("briefdescription")),
            "static": True,
            **parse_obidog_flags(xml_attribute)
        }
    return attributes


def parse_static_methods(class_value):
    static_methods = {}
    for xml_attribute in class_value.xpath(
        "sectiondef[@kind='public-static-func']/memberdef[@kind='function']"
    ):
        static_func = parse_function_from_xml(xml_attribute, method=True)
        if static_func:
            if static_func["name"] in static_methods:
                overload = static_methods[static_func["name"]]
                if overload["__type__"] == "method_overload" and overload["static"]:
                    overload["overloads"].append(static_func)
                else:
                    static_methods[static_func["name"]] = {
                        "__type__": "method_overload",
                        "name": static_func["name"],
                        "overloads": [overload, static_func],
                    }
            else:
                static_methods[static_func["name"]] = static_func
    return static_methods


def parse_class_from_xml(class_value):
    nobind = False
    class_name = extract_xml_value(class_value, "compoundname")
    if class_value.xpath("templateparamlist"):
        nobind = True
        #return class_name, None
    abstract = False
    if "abstract" in class_value.attrib and class_value.attrib["abstract"] == "yes":
        abstract = True
    base_classes_id = [
        item.attrib["refid"]
        for item in class_value.xpath(
            'inheritancegraph/node[@id = 1]/childnode[@relation="public-inheritance"]'
        )
    ]
    bases = []
    if base_classes_id:
        for base_class_id in base_classes_id:
            base = class_value.xpath(f"inheritancegraph/node[@id = {base_class_id}]")[0]
            bases.append(get_content(base).strip())
    base_location = class_value.xpath("location")[0].attrib["file"]
    location = os.path.relpath(
        os.path.normpath(base_location), os.path.normpath(PATH_TO_OBENGINE)
    ).replace(os.path.sep, "/")
    description = extract_xml_value(class_value, "briefdescription/para")

    class_methods = parse_methods(class_name, class_value)
    attributes = parse_attributes(class_value)
    static_methods = parse_static_methods(class_value)
    flags = parse_obidog_flags(class_value)

    CONFLICTS.append(class_name, class_value)
    return (
        class_name,
        {
            "__type__": "class",
            "name": class_name,
            "abstract": abstract,
            "bases": bases,
            "location": location,
            "description": description,
            "attributes": attributes,
            "static_methods": static_methods,
            "nobind": nobind,
            **class_methods,
            **flags,
        },
    )
