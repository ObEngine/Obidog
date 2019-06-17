from lxml import etree
from itertools import groupby

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
    return {
        "name": member_name,
        "definition": member_definition,
        "parameters": member_parameters,
        "description": member_description,
        "returnType": member_return_type
    }

def parse_class_from_xml(class_path):
    export = {}
    tree = etree.parse(class_path)
    export["name"] = extract_xml_value(tree, "/doxygen/compounddef/compoundname")
    if "obe::obe" in export["name"]: # Fixing nested namespace issue in Doxygen
        export["name"] = export["name"].replace("obe::obe::", "obe::")
    export["desc"] = extract_xml_value(tree, "/doxygen/compounddef/briefdescription/para")
    export["methods"] = {}
    if len(tree.xpath("/doxygen/compounddef/sectiondef[@kind='public-func']")) > 0:
        for xml_method in tree.xpath("/doxygen/compounddef/sectiondef[@kind='public-func']")[0]:
            #print("Parsing class", xml_method)
            method = parse_method_from_xml(xml_method)
            #print("Method export", method)
            export["methods"][method["name"]] = method
    return export["name"], export