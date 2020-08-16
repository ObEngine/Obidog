import os

from lxml import etree
from obidog.config import PATH_TO_OBENGINE
from obidog.parsers.utils.xml_utils import (
    get_content,
    get_content_if,
    extract_xml_value,
)
from obidog.parsers.function_parser import parse_function_from_xml
from obidog.parsers.parameters_parser import parse_parameters_from_xml
from obidog.parsers.globals_parser import parse_global_from_xml
from obidog.parsers.utils.doxygen_utils import doxygen_refid_to_cpp_name
from obidog.parsers.obidog_parser import parse_obidog_flags, CONFLICTS
from obidog.models.functions import (
    PlaceholderFunctionModel,
    FunctionOverloadModel,
    FunctionModel,
)
from obidog.models.enums import EnumModel, EnumValueModel
from obidog.models.typedefs import TypedefModel


def parse_functions_from_xml(namespace_name, namespace, cpp_db):
    functions_path = "sectiondef[@kind='func']/memberdef[@kind='function']"
    xml_functions = namespace.xpath(functions_path)
    for xml_function in xml_functions:
        function = parse_function_from_xml(xml_function)
        real_name = "::".join((namespace_name, function.name))
        if isinstance(function, FunctionModel):
            if real_name in cpp_db.functions:
                # Replace unusable existing function with usable function and force casting
                if isinstance(cpp_db.functions[real_name], PlaceholderFunctionModel):
                    function.force_cast = True
                    cpp_db.functions[real_name] = function
                else:
                    existing_function = cpp_db.functions[real_name]
                    if isinstance(existing_function, FunctionOverloadModel):
                        existing_function.overloads.append(function)
                    else:
                        cpp_db.functions[real_name] = FunctionOverloadModel(
                            name=existing_function.name,
                            overloads=[existing_function, function],
                        )
            else:
                cpp_db.functions[real_name] = function
        else:
            # Force cast as unusable function exists
            if real_name in cpp_db.functions:
                cpp_db.functions[real_name].force_cast = True
            # Add unusable function in db for later check
            else:
                cpp_db.functions[real_name] = function


def parse_typedef_from_xml(xml_typedef):
    typedef_name = get_content(xml_typedef.find("name"))
    if xml_typedef.find("type").find("ref") is not None:
        typedef_type = doxygen_refid_to_cpp_name(xml_typedef.find("type").find("ref"))
    else:
        typedef_type = get_content(xml_typedef.find("type"))

    typedef_description = get_content_if(
        xml_typedef.find("briefdescription").find("para")
    )
    typedef_location = get_content(xml_typedef.find("location"))
    typedef_definition = get_content(xml_typedef.find("definition"))
    CONFLICTS.append(typedef_name, xml_typedef)

    return TypedefModel(
        name=typedef_name,
        definition=typedef_definition,
        type=typedef_type,
        flags=parse_obidog_flags(xml_typedef),
        description=typedef_description,
        location=typedef_location,
    )


def parse_typedefs_from_xml(namespace_name, namespace, cpp_db):
    typedefs_path = "sectiondef[@kind='typedef']/memberdef[@kind='typedef']"
    xml_typedefs = namespace.xpath(typedefs_path)
    for xml_typedef in xml_typedefs:
        typedef = parse_typedef_from_xml(xml_typedef)
        cpp_db.typedefs["::".join((namespace_name, typedef.name))] = typedef


def parse_enum_from_xml(xml_enum):
    enum_name = get_content(xml_enum.find("name"))
    enum_description = get_content(xml_enum.find("briefdescription"))
    enum_values = []

    base_location = xml_enum.find("location").attrib["file"]
    location = os.path.relpath(
        os.path.normpath(base_location), os.path.normpath(PATH_TO_OBENGINE)
    ).replace(os.path.sep, "/")

    enum_values = []
    for enum_value in xml_enum.xpath("enumvalue"):
        enum_values.append(
            EnumValueModel(
                name=get_content(enum_value.find("name")),
                description=get_content(enum_value.find("briefdescription")),
            )
        )
    CONFLICTS.append(enum_name, xml_enum)
    return EnumModel(
        name=enum_name,
        values=enum_values,
        flags=parse_obidog_flags(xml_enum),
        description=enum_description,
        location=location,
    )


def parse_enums_from_xml(namespace_name, namespace, cpp_db):
    enums_path = "sectiondef[@kind='enum']/memberdef[@kind='enum']"
    xml_enums = namespace.xpath(enums_path)
    for xml_enum in xml_enums:
        enum = parse_enum_from_xml(xml_enum)
        cpp_db.enums["::".join((namespace_name, enum.name))] = enum


def parse_globals_from_xml(namespace_name, namespace, cpp_db):
    globals_path = "sectiondef[@kind='var']/memberdef[@kind='variable']"
    xml_globals = namespace.xpath(globals_path)
    for xml_global in xml_globals:
        cpp_global = parse_global_from_xml(xml_global)
        if cpp_global:
            cpp_db.globals["::".join((namespace_name, cpp_global.name))] = cpp_global


def parse_namespace_from_xml(class_path, cpp_db):
    tree = etree.parse(class_path)

    namespace = tree.xpath("/doxygen/compounddef")[0]
    namespace_name = extract_xml_value(namespace, "compoundname")

    cpp_db.namespaces[namespace_name] = parse_obidog_flags(namespace)

    parse_functions_from_xml(namespace_name, namespace, cpp_db)
    parse_typedefs_from_xml(namespace_name, namespace, cpp_db)
    parse_enums_from_xml(namespace_name, namespace, cpp_db)
    parse_globals_from_xml(namespace_name, namespace, cpp_db)
