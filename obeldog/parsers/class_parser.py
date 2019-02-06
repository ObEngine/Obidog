from lxml import etree

from obeldog.exceptions import ParameterNameNotFoundInXMLException

def get_content(node):
    return ''.join(node.itertext())

def get_content_if(node):
    if node != None:
        return ''.join(node.itertext())
    else:
        return None

def extract_xml_value(tree, path):
    if len(tree.xpath(path)) > 0:
        return get_content(tree.xpath(path)[0])
    else:
        return None

def parse_parameters_from_xml(xml_parameters):
    parameters = {}
    for xml_parameter in xml_parameters:
        parameter_declname = xml_parameter.find("declname")
        parameter_defname = xml_parameter.find("defname")
        if parameter_declname is not None:
            parameter_name = get_content(parameter_declname)
        elif parameter_defname is not None:
            parameter_name = get_content(parameter_defname)
        else:
            raise ParameterNameNotFoundInXMLException()
        parameters[parameter_name] = {
            "name": parameter_name,
            "type": get_content(xml_parameter.find("type")),
        }
        if get_content_if(xml_parameter.find("defval")):
            parameters[parameter_name]["default"] = get_content_if(xml_parameter.find("defval"))
        parameter_description = get_content_if(xml_parameter.find("briefdescription"))

        for xml_p_description in xml_parameter.xpath("detaileddescription/para/parameterlist/parameteritem"):
            if len(xml_p_description.xpath("parameternamelist/parametername")) > 0:
                if get_content(xml_p_description.find("parameternamelist").find("parametername")) == parameter_name:
                    parameter_description = get_content_if(xml_p_description.find("parameterdescription"))
        if parameter_description:
            if parameter_description.startswith("\n"):
                parameter_description = parameter_description.replace("\n", "", 1)
            parameters[parameter_name]["description"] = parameter_description
    return parameters

def parse_method_from_xml(xml_method):
    #print("Parsing method", xml_method)
    #import pdb; pdb.set_trace()
    #print("Parsing method member", xml_method)
    member_name = get_content(xml_method.find("name"))
    member_return_type = get_content(xml_method.find("type"))
    member_definition = get_content(xml_method.find("definition"))
    member_description = get_content_if(xml_method.find("briefdescription").find("para"))
    member_parameters = parse_parameters_from_xml(xml_method.xpath("param"))
    return {
        "name": member_name,
        "defintion": member_definition,
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