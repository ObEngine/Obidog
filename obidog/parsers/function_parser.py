from obidog.parsers.utils.xml_utils import get_content, get_content_if
from obidog.parsers.parameters_parser import parse_parameters_from_xml
from obidog.parsers.utils.doxygen_utils import doxygen_refid_to_cpp_name

def parse_function_from_xml(xml_function, method=False):
    name = get_content(xml_function.find("name"))
    if xml_function.find("type").find("ref") is not None:
        return_type = doxygen_refid_to_cpp_name(xml_function.find("type").find("ref"))
    else:
        return_type = get_content(xml_function.find("type"))
    if return_type != "" or method:
        definition = get_content(xml_function.find("definition"))
        description = get_content_if(xml_function.find("briefdescription").find("para"))
        parameters = parse_parameters_from_xml(xml_function)
        qualifiers = []
        if xml_function.attrib["const"] == "yes":
            qualifiers.append("const")
        if "volatile" in xml_function.attrib and xml_function.attrib["volatile"] == "yes":
            qualifiers.append("volatile")
        return {
            "__type__": "function" if not method else "method",
            "name": name,
            "definition": definition,
            "parameters": parameters,
            "description": description,
            "return_type": return_type,
            "qualifiers": qualifiers
        }
