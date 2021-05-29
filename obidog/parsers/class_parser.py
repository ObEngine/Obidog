import os

from obidog.config import PATH_TO_OBENGINE
from obidog.exceptions import ParameterNameNotFoundInXMLException
from obidog.models.classes import AttributeModel, ClassBaseModel, ClassModel
from obidog.models.flags import ObidogFlagsModel
from obidog.models.functions import (
    FunctionModel,
    FunctionOverloadModel,
    PlaceholderFunctionModel,
    FunctionVisibility,
)
from obidog.models.qualifiers import QualifiersModel
from obidog.parsers.function_parser import parse_function_from_xml
from obidog.parsers.location_parser import parse_doxygen_location
from obidog.parsers.obidog_parser import CONFLICTS, parse_obidog_flags
from obidog.parsers.utils.doxygen_utils import doxygen_refid_to_cpp_name
from obidog.parsers.utils.xml_utils import (
    extract_xml_value,
    get_content,
    get_content_if,
)


def parse_methods(class_name, class_value):
    methods = {}
    constructors = []
    destructor = None
    internal = {}
    all_methods = (
        class_value.xpath("sectiondef[@kind='public-func']/memberdef[@kind='function']")
        + class_value.xpath(
            "sectiondef[@kind='public-static-func']/memberdef[@kind='function']"
        )
        + class_value.xpath(
            "sectiondef[@kind='protected-func']/memberdef[@kind='function']"
        )
        + class_value.xpath(
            "sectiondef[@kind='private-func']/memberdef[@kind='function']"
        )
    )

    if not all_methods:
        return methods, constructors, destructor, internal
    for xml_method in all_methods:
        method = parse_function_from_xml(xml_method, is_method=True)
        method.from_class = class_name
        if method.visibility == FunctionVisibility.Public:
            # Method has class name => Constructor
            if method.name == class_name and isinstance(method, FunctionModel):
                constructors.append(method)
                continue
            # Method has ~class name => Destructor
            elif method.name == f"~{class_name}" and isinstance(method, FunctionModel):
                destructor = method
                continue
            # Method has no return type, probably a tricky case such as reusing a parent class constructor
            if isinstance(method, FunctionModel) and not method.return_type:
                continue
            function_dest = methods
        else:
            # Method is protected / private => Implementation details
            # This won't be used for details but can be used for some details
            # Such as knowing whether a class is abstract or not
            function_dest = internal
        # Method not already in methods dict
        if not method.name in function_dest:
            function_dest[method.name] = method
        else:
            # Replace unusable method with usable overload and force casting
            if isinstance(function_dest[method.name], PlaceholderFunctionModel):
                method.force_cast = True
                function_dest[method.name] = method
            # Create a function overload
            else:
                overload = function_dest[method.name]
                if isinstance(overload, FunctionOverloadModel):
                    overload.overloads.append(method)
                    if method.flags.bind_to:
                        overload.flags.bind_to = method.bind_to
                else:
                    function_dest[method.name] = FunctionOverloadModel(
                        name=method.name,
                        overloads=[overload, method],
                        flags=ObidogFlagsModel(
                            bind_to=overload.flags.bind_to or method.flags.bind_to
                        ),
                    )

    return methods, constructors, destructor, internal


def parse_attributes(class_value):
    attributes = {}
    all_xml_attributes = {
        False: class_value.xpath(
            "sectiondef[@kind='public-attrib']/memberdef[@kind='variable']"
        ),
        True: class_value.xpath(
            "sectiondef[@kind='public-static-attrib']/memberdef[@kind='variable']"
        ),
    }
    for is_static, xml_attributes in all_xml_attributes.items():
        for xml_attribute in xml_attributes:
            attribute_name = get_content(xml_attribute.find("name"))
            # Ignore unions
            if attribute_name.startswith("@"):
                continue
            attribute_type = get_content(xml_attribute.find("type"))
            attribute_desc = get_content(xml_attribute.find("briefdescription"))
            qualifiers = QualifiersModel(static=is_static)
            flags = parse_obidog_flags(xml_attribute)
            templated = False
            if xml_attribute.find("templateparamlist") is not None:
                templated = True
            if not templated:
                attributes[attribute_name] = AttributeModel(
                    name=attribute_name,
                    type=attribute_type,
                    qualifiers=qualifiers,
                    description=attribute_desc,
                    flags=flags,
                )

    return attributes


def parse_class_from_xml(class_value) -> ClassModel:
    nobind = False
    class_name = extract_xml_value(class_value, "compoundname")
    namespace_name, class_name = (
        "::".join(class_name.split("::")[:-1:]),
        class_name.split("::")[-1],
    )
    # Ignore template classes
    if class_value.xpath("templateparamlist"):
        nobind = True
    abstract = False
    if "abstract" in class_value.attrib and class_value.attrib["abstract"] == "yes":
        abstract = True

    # Fetching parents
    base_classes_id = [
        item.attrib["refid"]
        for item in class_value.xpath(
            'inheritancegraph/node[@id = 1]/childnode[@relation="public-inheritance"]'
        )
    ]
    bases = []
    if base_classes_id:
        for base_class_id in base_classes_id:
            base = class_value.xpath(f"inheritancegraph/node[@id = {base_class_id}]")[0]
            bases.append(get_content(base).strip())

    description = extract_xml_value(class_value, "briefdescription/para")

    methods, constructors, destructor, internal = parse_methods(
        class_name.split("::")[-1], class_value
    )
    attributes = parse_attributes(class_value)
    flags = parse_obidog_flags(
        class_value, symbol_name="::".join([namespace_name, class_name])
    )
    flags.nobind = flags.nobind or nobind

    CONFLICTS.append(class_name, class_value)
    return ClassModel(
        name=class_name,
        namespace=namespace_name,
        abstract=abstract,
        bases=bases,
        attributes=attributes,
        constructors=constructors,
        destructor=destructor,
        methods=methods,
        internal=internal,
        flags=flags,
        description=description,
        location=parse_doxygen_location(class_value),
    )
