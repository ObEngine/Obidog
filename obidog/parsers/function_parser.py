from obidog.logger import log
from obidog.models.base import ItemVisibility
from obidog.models.functions import FunctionModel, FunctionPlaceholderModel
from obidog.models.qualifiers import QualifiersModel
from obidog.parsers.location_parser import parse_doxygen_location
from obidog.parsers.obidog_parser import get_cpp_element_obidog_flags
from obidog.parsers.parameters_parser import parse_parameters_from_xml
from obidog.parsers.utils.cpp_utils import parse_definition
from obidog.parsers.utils.doxygen_utils import (
    doxygen_id_to_cpp_id,
    doxygen_ref_to_cpp_name,
)
from obidog.parsers.utils.xml_utils import get_content, get_content_if
from obidog.utils.cpp_utils import sanitize_cpp_definition


def make_return_type(return_type):
    full_return_type = ""
    for return_type_part in return_type.iter():
        if return_type_part.tag == "ref":
            full_return_type += doxygen_ref_to_cpp_name(return_type_part)
        elif return_type_part.text:
            full_return_type += return_type_part.text
        if return_type_part.tail:
            tail = return_type_part.tail
            if tail and tail.strip() == "":
                full_return_type += " "
            else:
                full_return_type += return_type_part.tail
    return sanitize_cpp_definition(full_return_type)


def parse_function_from_xml(xml_function, doxygen_index, is_method: bool = False):
    function_id = doxygen_id_to_cpp_id(xml_function.attrib["id"])
    name = get_content(xml_function.find("name"))
    deleted = False
    if (
        get_content(xml_function.find("argsstring"))
        .replace(" ", "")
        .endswith("=delete")
    ):
        deleted = True
    templated = False
    visibility = ItemVisibility(xml_function.attrib["prot"])
    if (
        "<" in name and ">" in name and "<=>" not in name
    ):  # Template specialisation is ignored
        return FunctionPlaceholderModel(
            name=name, namespace="", visibility=visibility
        )  # note: do we need namespace here ?
    if name.startswith("operator") and not is_method:  # TODO: Improve matching
        return FunctionPlaceholderModel(
            name=name, namespace="", visibility=visibility
        )  # note: do we need to inject namespace here ?
    return_type = make_return_type(xml_function.find("type"))
    if not return_type and not is_method:
        return FunctionPlaceholderModel(name=name, namespace="", visibility=visibility)
    if xml_function.find("templateparamlist") is not None:
        templated = True
    definition = get_content(xml_function.find("definition"))
    description = get_content_if(xml_function.find("briefdescription").find("para"))
    parameters = parse_parameters_from_xml(xml_function, doxygen_index)
    qualifiers = QualifiersModel()
    if xml_function.attrib["const"] == "yes":
        qualifiers.const = True
    if "volatile" in xml_function.attrib and xml_function.attrib["volatile"] == "yes":
        qualifiers.volatile = True
    if xml_function.attrib["static"] == "yes":
        qualifiers.static = True
    abstract = False
    if xml_function.attrib["virt"] == "pure-virtual":
        abstract = True

    identifier = parse_definition(definition)[1]
    if is_method:
        if " " in identifier:
            identifier = identifier.split(" ")[0]
        namespace = "::".join(identifier.split("::")[:-2])
    else:
        namespace = "::".join(identifier.split("::")[:-1])

    flags = get_cpp_element_obidog_flags(function_id)
    if flags.nobind:
        return FunctionPlaceholderModel(
            name=name, namespace=namespace, visibility=visibility
        )

    for rename_parameter in flags.rename_parameters:
        found_parameter = False
        for parameter in parameters:
            if parameter.name == rename_parameter[0]:
                parameter.name = rename_parameter[1]
                found_parameter = True
                break
        if not found_parameter:
            log.warn(
                f"Could not find parameter to rename '{rename_parameter[0]}'"
                f" in function '{namespace}::{name}'"
            )

    return FunctionModel(
        id=function_id,
        name=name,
        namespace=namespace,
        definition=definition,
        parameters=parameters,
        return_type=return_type,
        template=templated,
        qualifiers=qualifiers,
        flags=flags,
        description=description or "",
        deleted=deleted,
        abstract=abstract,
        visibility=visibility,
        location=parse_doxygen_location(xml_function),
    )
