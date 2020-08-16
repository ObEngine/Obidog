import os

from obidog.config import PATH_TO_OBENGINE
from obidog.exceptions import ParameterNameNotFoundInXMLException
from obidog.parsers.utils.xml_utils import (
    get_content,
    get_content_if,
    extract_xml_value,
)
from obidog.parsers.utils.doxygen_utils import doxygen_refid_to_cpp_name
from obidog.parsers.function_parser import parse_function_from_xml
from obidog.parsers.obidog_parser import parse_obidog_flags, CONFLICTS
from obidog.models.functions import (
    FunctionModel,
    PlaceholderFunctionModel,
    FunctionOverloadModel,
)
from obidog.models.qualifiers import QualifiersModel
from obidog.models.flags import ObidogFlagsModel
from obidog.models.classses import AttributeModel, ClassModel, ClassBaseModel


def parse_methods(class_name, class_value):
    methods = {}
    constructors = []
    destructor = None
    all_methods = class_value.xpath(
        "sectiondef[@kind='public-func']/memberdef[@kind='function']"
    ) + class_value.xpath(
        "sectiondef[@kind='public-static-func']/memberdef[@kind='function']"
    )

    if not all_methods:
        return methods, constructors, destructor
    for xml_method in all_methods:
        method = parse_function_from_xml(xml_method, method=True)
        # Method has class name => Constructor
        if method.name == class_name and isinstance(method, FunctionModel):
            constructors.append(method)
            continue
        # Method has ~class name => Destructor
        elif method.name == f"~{class_name}" and isinstance(method, FunctionModel):
            destructor = method
            continue
        # Method not already in methods dict
        if not method.name in methods:
            methods[method.name] = method
        else:
            # Replace unusable method with usable overload and force casting
            if isinstance(methods[method.name], PlaceholderFunctionModel):
                method.force_cast = True
                methods[method.name] = method
            # Create a function overload
            else:
                overload = methods[method.name]
                if isinstance(overload, FunctionOverloadModel):
                    overload.overloads.append(method)
                    if method.flags.bind_to:
                        overload.flags.bind_to = method.bind_to
                else:
                    methods[method.name] = FunctionOverloadModel(
                        name=method.name,
                        overloads=[overload, method],
                        flags=ObidogFlagsModel(
                            bind_to=overload.flags.bind_to or method.flags.bind_to
                        ),
                    )

    return methods, constructors, destructor


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
            attribute_type = get_content(xml_attribute.find("type"))
            attribute_desc = get_content(xml_attribute.find("briefdescription"))
            qualifiers = QualifiersModel(static=is_static)
            flags = parse_obidog_flags(xml_attribute)
            attributes[attribute_name] = AttributeModel(
                name=attribute_name,
                type=attribute_type,
                qualifiers=qualifiers,
                description=attribute_desc,
                flags=flags,
            )

    return attributes


def parse_class_from_xml(class_value):
    nobind = False
    class_name = extract_xml_value(class_value, "compoundname")
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

    # Fetching location
    base_location = class_value.xpath("location")[0].attrib["file"]
    location = os.path.relpath(
        os.path.normpath(base_location), os.path.normpath(PATH_TO_OBENGINE)
    ).replace(os.path.sep, "/")

    description = extract_xml_value(class_value, "briefdescription/para")

    methods, constructors, destructor = parse_methods(
        class_name.split("::")[-1], class_value
    )
    attributes = parse_attributes(class_value)
    flags = parse_obidog_flags(class_value)
    flags.nobind = flags.nobind or nobind

    CONFLICTS.append(class_name, class_value)
    return ClassModel(
        name=class_name,
        abstract=abstract,
        bases=bases,
        attributes=attributes,
        constructors=constructors,
        destructor=destructor,
        methods=methods,
        flags=flags,
        description=description,
        location=location,
    )
