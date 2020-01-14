from obeldog.exceptions import ParameterNameNotFoundInXMLException
from obeldog.parsers.utils.xml_utils import get_content, get_content_if
from obeldog.parsers.utils.doxygen_utils import doxygen_refid_to_cpp_name

def parse_parameters_from_xml(xml_function):
    parameters = []
    for xml_parameter in xml_function.xpath("param"):
        parameter_declname = xml_parameter.find("declname")
        parameter_defname = xml_parameter.find("defname")
        if parameter_declname is not None:
            parameter_name = get_content(parameter_declname)
        elif parameter_defname is not None:
            parameter_name = get_content(parameter_defname)
        else:
            raise ParameterNameNotFoundInXMLException()
        if xml_parameter.find("type").find("ref") is not None:
            parameter_return_type = doxygen_refid_to_cpp_name(xml_parameter.find("type").find("ref"))
            parameter_return_type = get_content(xml_parameter.find("type")).replace(
                get_content(xml_parameter.find("type").find("ref")),
                parameter_return_type
            )
        else:
            parameter_return_type = get_content(xml_parameter.find("type"))
        parameter = {
            "name": parameter_name,
            "type": parameter_return_type,
        }
        if get_content_if(xml_parameter.find("defval")):
            parameter["default"] = get_content_if(xml_parameter.find("defval"))
        parameter_description = get_content_if(xml_parameter.find("briefdescription"))

        for xml_p_description in xml_function.xpath("detaileddescription/para/parameterlist/parameteritem"):
            if len(xml_p_description.xpath("parameternamelist/parametername")) > 0:
                if get_content(xml_p_description.find("parameternamelist").find("parametername")) == parameter_name:
                    parameter_description = get_content_if(xml_p_description.find("parameterdescription"))
        if parameter_description:
            if parameter_description.startswith("\n"):
                parameter_description = parameter_description.replace("\n", "", 1)
            parameter["description"] = parameter_description
        parameters.append(parameter)
    return parameters