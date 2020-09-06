import os

from obidog.config import PATH_TO_OBENGINE
from obidog.models.functions import FunctionModel, PlaceholderFunctionModel
from obidog.models.location import Location
from obidog.models.qualifiers import QualifiersModel
from obidog.parsers.location_parser import parse_doxygen_location
from obidog.parsers.obidog_parser import CONFLICTS, parse_obidog_flags
from obidog.parsers.parameters_parser import parse_parameters_from_xml
from obidog.parsers.utils.doxygen_utils import doxygen_refid_to_cpp_name
from obidog.parsers.utils.xml_utils import get_content, get_content_if


def make_return_type(return_type):
    full_return_type = ""
    for return_type_part in return_type.iter():
        if return_type_part.tag == "ref":
            full_return_type += doxygen_refid_to_cpp_name(return_type_part)
        elif return_type_part.text:
            full_return_type += return_type_part.text.strip()
        if return_type_part.tail:
            tail = return_type_part.tail
            if tail and tail.strip() == "":
                full_return_type += " "
            else:
                full_return_type += return_type_part.tail.strip()
    return full_return_type


def parse_function_from_xml(xml_function, method=False):
    name = get_content(xml_function.find("name"))
    templated = False
    if (
        "<" in name and ">" in name and "<=>" not in name
    ):  # Template specialisation is ignored
        return PlaceholderFunctionModel(name)
    if name.startswith("operator") and not method:  # TODO: Improve matching
        return PlaceholderFunctionModel(name)
    return_type = make_return_type(xml_function.find("type"))
    if not return_type and not method:
        return PlaceholderFunctionModel(name)
    flags = parse_obidog_flags(xml_function)
    if flags.nobind:
        return PlaceholderFunctionModel(name)
    if xml_function.find("templateparamlist") is not None:
        templated = True
    definition = get_content(xml_function.find("definition"))
    description = get_content_if(xml_function.find("briefdescription").find("para"))
    parameters = parse_parameters_from_xml(xml_function)
    qualifiers = QualifiersModel()
    if xml_function.attrib["const"] == "yes":
        qualifiers.const = True
    if "volatile" in xml_function.attrib and xml_function.attrib["volatile"] == "yes":
        qualifiers.volatile = True
    if xml_function.attrib["static"] == "yes":
        qualifiers.static = True

    if not method:
        CONFLICTS.append(name, xml_function)

    if method:
        if " " in definition:
            namespace = "::".join(definition.split(" ")[1].split("::")[:-2:])
        else:
            namespace = "::".join(definition.split("::")[:-2:])  # Constructors
    elif " " in definition:
        namespace = "::".join(definition.split(" ")[1].split("::")[:-1:])
    else:
        raise NotImplementedError("Invalid case")

    return FunctionModel(
        name=name,
        namespace=namespace,
        definition=definition,
        parameters=parameters,
        return_type=return_type,
        template=templated,
        qualifiers=qualifiers,
        flags=flags,
        description=description,
        location=parse_doxygen_location(xml_function),
    )
