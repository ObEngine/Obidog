from obidog.models.functions import ParameterModel
from obidog.parsers.type_parser import parse_real_type
from obidog.parsers.utils.xml_utils import get_content, get_content_if


def parse_parameters_from_xml(xml_function, doxygen_index):
    parameters = []
    for index, xml_parameter in enumerate(xml_function.xpath("param")):
        parameter_declname = xml_parameter.find("declname")
        parameter_defname = xml_parameter.find("defname")
        if parameter_declname is not None:
            parameter_name = get_content(parameter_declname)
        elif parameter_defname is not None:
            parameter_name = get_content(parameter_defname)
        else:
            parameter_name = f"p{index}"
            # raise ParameterNameNotFoundInXMLException()

        parameter_return_type = parse_real_type(xml_parameter, doxygen_index)

        parameter = ParameterModel(name=parameter_name, type=parameter_return_type)
        if get_content_if(xml_parameter.find("defval")):
            parameter.default = get_content_if(xml_parameter.find("defval"))
        parameter_description = get_content_if(xml_parameter.find("briefdescription"))
        # LATER: Handle templated parameters (Discard ?)
        for xml_p_description in xml_function.xpath(
            "detaileddescription/para/parameterlist/parameteritem"
        ):
            if len(xml_p_description.xpath("parameternamelist/parametername")) > 0:
                if (
                    get_content(
                        xml_p_description.find("parameternamelist").find(
                            "parametername"
                        )
                    )
                    == parameter_name
                ):
                    parameter_description = get_content_if(
                        xml_p_description.find("parameterdescription")
                    )
        if parameter_description:
            if parameter_description.startswith("\n"):
                parameter_description = parameter_description.replace("\n", "", 1)
            parameter.description = parameter_description
        parameters.append(parameter)
    return parameters
