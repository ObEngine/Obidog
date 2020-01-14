from lxml import etree
import os

from obeldog.config import PATH_TO_OBENGINE
from obeldog.exceptions import ParameterNameNotFoundInXMLException
from obeldog.parsers.utils.xml_utils import get_content, get_content_if, extract_xml_value
from obeldog.parsers.utils.doxygen_utils import doxygen_refid_to_cpp_name
from obeldog.parsers.parameters_parser import parse_parameters_from_xml


def parse_method_from_xml(xml_method):
    #print("Parsing method", xml_method)
    #import pdb; pdb.set_trace()
    #print("Parsing method member", xml_method)
    member_name = get_content(xml_method.find("name"))
    #print("Member name", member_name)
    if xml_method.find("type").find("ref") is not None:
        member_return_type = doxygen_refid_to_cpp_name(xml_method.find("type").find("ref"))
    else:
        member_return_type = get_content(xml_method.find("type"))
    member_definition = get_content(xml_method.find("definition"))
    member_description = get_content_if(xml_method.find("briefdescription").find("para"))
    member_parameters = parse_parameters_from_xml(xml_method)
    member_qualifiers = []
    if xml_method.attrib["const"] == "yes":
        member_qualifiers.append("const")
    if "volatile" in xml_method.attrib and xml_method.attrib["volatile"] == "yes":
        member_qualifiers.append("volatile")
    return {
        "__type__": "method",
        "name": member_name,
        "definition": member_definition,
        "parameters": member_parameters,
        "description": member_description,
        "return_type": member_return_type,
        "qualifiers": member_qualifiers
    }

def parse_class_from_xml(class_path):
    export = {}
    tree = etree.parse(class_path)
    export["__type__"] = "class"
    export["name"] = extract_xml_value(tree, "/doxygen/compounddef/compoundname")
    base_location = tree.xpath("/doxygen/compounddef/location")[0].attrib["file"]
    export["location"] = os.path.relpath(
        os.path.normpath(base_location),
        os.path.normpath(PATH_TO_OBENGINE)
    ).replace(os.path.sep, "/")
    export["herits"] = []
    for basecompoundref in tree.xpath("/doxygen/compounddef/basecompoundref"):
        export["herits"].append(get_content(basecompoundref))
    if "obe::obe" in export["name"]: # Fixing nested namespace issue in Doxygen
        export["name"] = export["name"].replace("obe::obe::", "obe::")
    export["desc"] = extract_xml_value(tree, "/doxygen/compounddef/briefdescription/para")
    export["methods"] = {}
    export["constructors"] = []
    if len(tree.xpath("/doxygen/compounddef/sectiondef[@kind='public-func']")) > 0:
        for xml_method in tree.xpath("/doxygen/compounddef/sectiondef[@kind='public-func']")[0]:
            #print("Parsing class", xml_method)
            method = parse_method_from_xml(xml_method)
            #print("Method export", method)
            if method["name"] == export["name"].split("::")[-1]:
                export["constructors"].append(method)
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