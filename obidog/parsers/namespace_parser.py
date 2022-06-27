from lxml import etree

from obidog.parsers.utils.xml_utils import (
    get_content,
    get_content_if,
    extract_xml_value,
)
from obidog.parsers.function_parser import parse_function_from_xml
from obidog.parsers.globals_parser import parse_global_from_xml
from obidog.parsers.location_parser import parse_doxygen_location
from obidog.parsers.obidog_parser import parse_obidog_flags, CONFLICTS
from obidog.parsers.type_parser import parse_real_type, rebuild_incomplete_type
from obidog.models.functions import (
    PlaceholderFunctionModel,
    FunctionOverloadModel,
    FunctionModel,
)
from obidog.models.enums import EnumModel, EnumValueModel
from obidog.models.typedefs import TypedefModel
from obidog.models.namespace import NamespaceModel


def parse_functions_from_xml(namespace_name, namespace, cpp_db, doxygen_index):
    functions_path = "sectiondef[@kind='func']/memberdef[@kind='function']"
    xml_functions = namespace.xpath(functions_path)
    for xml_function in xml_functions:
        function = parse_function_from_xml(xml_function, doxygen_index)
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
                            namespace=existing_function.namespace,
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


def parse_typedef_from_xml(namespace_name, xml_typedef, doxygen_index):
    typedef_name = get_content(xml_typedef.find("name"))
    typedef_type = parse_real_type(xml_typedef, doxygen_index)
    typedef_type = rebuild_incomplete_type(typedef_type, namespace_name, doxygen_index)

    typedef_description = get_content_if(
        xml_typedef.find("briefdescription").find("para")
    )
    typedef_definition = get_content(xml_typedef.find("definition"))
    CONFLICTS.append(typedef_name, xml_typedef)

    return TypedefModel(
        name=typedef_name,
        namespace=namespace_name,
        definition=typedef_definition,
        type=typedef_type,
        flags=parse_obidog_flags(xml_typedef),
        description=typedef_description,
        location=parse_doxygen_location(xml_typedef),
    )


def parse_typedefs_from_xml(namespace_name, namespace, cpp_db, doxygen_index):
    typedefs_path = "sectiondef[@kind='typedef']/memberdef[@kind='typedef']"
    xml_typedefs = namespace.xpath(typedefs_path)
    for xml_typedef in xml_typedefs:
        typedef = parse_typedef_from_xml(namespace_name, xml_typedef, doxygen_index)
        full_name = "::".join((namespace_name, typedef.name))
        cpp_db.typedefs[full_name] = typedef
        cpp_db.typedefs[full_name].namespace = namespace_name


def parse_enum_from_xml(xml_enum):
    enum_name = get_content(xml_enum.find("name"))
    enum_description = get_content(xml_enum.find("briefdescription"))

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
        location=parse_doxygen_location(xml_enum),
    )


def parse_enums_from_xml(namespace_name, namespace, cpp_db):
    namespace_kind = namespace.attrib["kind"]
    from_section = "enum" if namespace_kind == "namespace" else "public-type"
    enums_path = f"sectiondef[@kind='{from_section}']/memberdef[@kind='enum']"
    xml_enums = namespace.xpath(enums_path)
    for xml_enum in xml_enums:
        enum = parse_enum_from_xml(xml_enum)
        full_name = "::".join((namespace_name, enum.name))
        cpp_db.enums[full_name] = enum
        cpp_db.enums[full_name].namespace = namespace_name


def parse_globals_from_xml(namespace_name, namespace, cpp_db, doxygen_index):
    globals_path = "sectiondef[@kind='var']/memberdef[@kind='variable']"
    xml_globals = namespace.xpath(globals_path)
    for xml_global in xml_globals:
        cpp_global = parse_global_from_xml(xml_global, doxygen_index)
        if cpp_global:
            full_name = "::".join((namespace_name, cpp_global.name))
            cpp_db.globals[full_name] = cpp_global
            cpp_db.globals[full_name].namespace = namespace_name


def parse_namespace_from_xml(xml_path, cpp_db, doxygen_index):
    tree = etree.parse(xml_path)

    namespace = tree.xpath("/doxygen/compounddef")[0]
    namespace_name = extract_xml_value(namespace, "compoundname")
    namespace_description = extract_xml_value(namespace, "briefdescription")
    # TODO: Parse namespace description

    flags = parse_obidog_flags(namespace, symbol_name=namespace_name)

    cpp_db.namespaces[namespace_name] = NamespaceModel(
        name=namespace_name.split("::")[-1],
        path=namespace_name,
        namespace="::".join(namespace_name.split("::")[:-1:]),
        description=namespace_description,
        flags=flags,
    )

    if flags.nobind:
        return

    parse_functions_from_xml(namespace_name, namespace, cpp_db, doxygen_index)
    parse_typedefs_from_xml(namespace_name, namespace, cpp_db, doxygen_index)
    parse_enums_from_xml(namespace_name, namespace, cpp_db)
    parse_globals_from_xml(namespace_name, namespace, cpp_db, doxygen_index)

    cpp_db.namespaces[namespace_name].functions = {
        function_name: function
        for function_name, function in cpp_db.functions.items()
        if (
            isinstance(function, FunctionModel) and function.namespace == namespace_name
        )
        or (
            isinstance(function, FunctionOverloadModel)
            and function.overloads[0].namespace == namespace_name
        )
    }
    cpp_db.namespaces[namespace_name].typedefs = {
        typedef_name: typedef
        for typedef_name, typedef in cpp_db.typedefs.items()
        if typedef.namespace == namespace_name
    }
    cpp_db.namespaces[namespace_name].enums = {
        enum_name: enum
        for enum_name, enum in cpp_db.enums.items()
        if enum.namespace == namespace_name
    }
    cpp_db.namespaces[namespace_name].globals = {
        global_name: glob
        for global_name, glob in cpp_db.globals.items()
        if glob.namespace == namespace_name
    }
