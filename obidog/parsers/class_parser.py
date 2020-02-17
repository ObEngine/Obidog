from lxml import etree
import os

from obidog.config import PATH_TO_OBENGINE
from obidog.exceptions import ParameterNameNotFoundInXMLException
from obidog.parsers.utils.xml_utils import get_content, get_content_if, extract_xml_value
from obidog.parsers.utils.doxygen_utils import doxygen_refid_to_cpp_name
from obidog.parsers.function_parser import parse_function_from_xml


def parse_class_from_xml(class_path):
    export = {}
    tree = etree.parse(class_path)
    export["__type__"] = "class"
    export["name"] = extract_xml_value(tree, "/doxygen/compounddef/compoundname")
    base_classes = tree.xpath("/doxygen/compounddef/basecompoundref")
    if base_classes:
        export["bases"] = [get_content(base) for base in base_classes]
    base_location = tree.xpath("/doxygen/compounddef/location")[0].attrib["file"]
    export["location"] = os.path.relpath(
        os.path.normpath(base_location),
        os.path.normpath(PATH_TO_OBENGINE)
    ).replace(os.path.sep, "/")
    export["bases"] = []
    for basecompoundref in tree.xpath("/doxygen/compounddef/basecompoundref"):
        export["bases"].append(get_content(basecompoundref))
    if "obe::obe" in export["name"]: # Fixing nested namespace issue in Doxygen
        export["name"] = export["name"].replace("obe::obe::", "obe::")
    export["desc"] = extract_xml_value(tree, "/doxygen/compounddef/briefdescription/para")
    export["methods"] = {}
    export["constructors"] = []
    if len(tree.xpath("/doxygen/compounddef/sectiondef[@kind='public-func']")) > 0:
        for xml_method in tree.xpath("/doxygen/compounddef/sectiondef[@kind='public-func']")[0]:
            #print("Parsing class", xml_method)
            method = parse_function_from_xml(xml_method, method=True)
            #print("Method export", method)
            if method["name"] == export["name"].split("::")[-1]:
                export["constructors"].append(method)
            elif method["name"] == f"~{export['name'].split('::')[-1]}":
                export["destructor"] = method
            else:
                if method["name"] in export["methods"]:
                    overload = export["methods"][method["name"]]
                    if overload["__type__"] == "method_overload":
                        overload["overloads"].append(method)
                    else:
                        export["methods"][method["name"]] = {
                            "__type__": "method_overload",
                            "name": method["name"],
                            "overloads": [overload, method]
                        }
                else:
                    export["methods"][method["name"]] = method
    export["attributes"] = {}
    for xml_attribute in tree.xpath(
        "/doxygen/compounddef/sectiondef[@kind='public-attrib']/memberdef[@kind='variable']"
    ):
        attribute_name = get_content(xml_attribute.find("name"))
        export["attributes"][attribute_name] = {
            "__type__": "attribute",
            "type": get_content(xml_attribute.find("type")),
            "name": attribute_name,
            "description": get_content(xml_attribute.find("briefdescription"))
        }
    return export["name"], export