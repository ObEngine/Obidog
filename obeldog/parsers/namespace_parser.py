from lxml import etree
from obeldog.parsers.utils.xml_utils import get_content, get_content_if, extract_xml_value
from obeldog.parsers.parameters_parser import parse_parameters_from_xml
from obeldog.parsers.utils.doxygen_utils import doxygen_refid_to_cpp_name

def parse_function_from_xml(xml_function): # TODO: Use this function for methods too
    function_name = get_content(xml_function.find("name"))
    if xml_function.find("type").find("ref") is not None:
        function_return_type = doxygen_refid_to_cpp_name(xml_function.find("type").find("ref"))
    else:
        function_return_type = get_content(xml_function.find("type"))
    if function_return_type != "":
        function_description = get_content_if(xml_function.find("briefdescription").find("para"))
        function_definition = get_content(xml_function.find("definition"))
        function_parameters = parse_parameters_from_xml(xml_function)
        return {
            "name": function_name,
            "definition": function_definition,
            "parameters": function_parameters,
            "description": function_description,
            "return_type": function_return_type
        }
    else:
        return None

def parse_functions_from_xml(namespace, tree, cpp_db):
    functions_path = "/doxygen/compounddef/sectiondef[@kind='func']/memberdef[@kind='function']"
    xml_functions = tree.xpath(functions_path)
    for xml_function in xml_functions:
        function = parse_function_from_xml(xml_function)
        if function:
            cpp_db.functions["::".join((namespace, function["name"]))] = function


def parse_typedef_from_xml(xml_typedef):
    typedef_name = get_content(xml_typedef.find("name"))
    if xml_typedef.find("type").find("ref") is not None:
        typedef_type = doxygen_refid_to_cpp_name(xml_typedef.find("type").find("ref"))
    else:
        typedef_type = get_content(xml_typedef.find("type"))

    typedef_description = get_content_if(xml_typedef.find("briefdescription").find("para"))
    typedef_definition = get_content(xml_typedef.find("definition"))
    typedef_parameters = parse_parameters_from_xml(xml_typedef)

    return {
        "name": typedef_name,
        "definition": typedef_definition,
        "parameters": typedef_parameters,
        "description": typedef_description,
        "returnType": typedef_type
    }

def parse_typedefs_from_xml(namespace, tree, cpp_db):
    typedefs_path = "/doxygen/compounddef/sectiondef[@kind='typedef']/memberdef[@kind='typedef']"
    xml_typedefs = tree.xpath(typedefs_path)
    for xml_typedef in xml_typedefs:
        typedef = parse_typedef_from_xml(xml_typedef)
        if typedef:
            cpp_db.typedefs["::".join((namespace, typedef["name"]))] = typedef

def parse_enum_from_xml(xml_enum):
    enum_name = get_content(xml_enum.find("name"))
    enum_description = get_content(xml_enum.find("briefdescription"))
    enum_values = []
    for enum_value in xml_enum.xpath("enumvalue"):
        enum_values.append({
            "name": get_content(enum_value.find("name")),
            "description": get_content(enum_value.find("briefdescription"))
        })
    return {
        "name": enum_name,
        "description": enum_description,
        "values": enum_values
    }

def parse_enums_from_xml(namespace, tree, cpp_db):
    enums_path = "/doxygen/compounddef/sectiondef[@kind='enum']/memberdef[@kind='enum']"
    xml_enums = tree.xpath(enums_path)
    for xml_enum in xml_enums:
        enum = parse_enum_from_xml(xml_enum)
        if enum:
            cpp_db.enums["::".join((namespace, enum["name"]))] = enum

def parse_namespace_from_xml(class_path, cpp_db):
    tree = etree.parse(class_path)
    namespace_name = extract_xml_value(tree, "/doxygen/compounddef/compoundname")
    print(f"Namespace : {namespace_name}")
    parse_functions_from_xml(namespace_name, tree, cpp_db)
    parse_typedefs_from_xml(namespace_name, tree, cpp_db)
    parse_enums_from_xml(namespace_name, tree, cpp_db)
    print("End")