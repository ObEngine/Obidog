from obidog.models.base import ItemVisibility
from obidog.models.classes import AttributeModel, ClassModel
from obidog.models.flags import MetaTag, ObidogFlagsModel
from obidog.models.functions import (
    FunctionModel,
    FunctionOverloadModel,
    PlaceholderFunctionModel,
)
from obidog.models.qualifiers import QualifiersModel
from obidog.parsers.function_parser import parse_function_from_xml
from obidog.parsers.location_parser import parse_doxygen_location
from obidog.parsers.obidog_parser import CONFLICTS, parse_obidog_flags
from obidog.parsers.type_parser import (
    parse_cpp_type,
    parse_real_type,
    rebuild_incomplete_type,
)
from obidog.parsers.utils.cpp_utils import parse_definition
from obidog.parsers.utils.xml_utils import (
    extract_xml_value,
    get_content,
    get_content_if,
)
from obidog.utils.cpp_utils import make_fqn


def parse_methods(class_name, class_value, doxygen_index):
    methods = {}
    constructors = []
    destructor = None
    private_methods = {}
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
        return methods, constructors, destructor, private_methods
    for xml_method in all_methods:
        method = parse_function_from_xml(xml_method, doxygen_index, is_method=True)
        method.from_class = class_name
        if method.visibility == ItemVisibility.Public:
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
            function_dest = private_methods
        # Method not already in methods dict
        if method.name not in function_dest:
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
                    if method.flags.rename:
                        overload.flags.rename = method.rename
                else:
                    function_dest[method.name] = FunctionOverloadModel(
                        name=method.name,
                        namespace=overload.namespace,
                        from_class=overload.from_class,
                        overloads=[overload, method],
                        flags=ObidogFlagsModel(
                            rename=overload.flags.rename or method.flags.rename
                        ),
                    )

    return methods, constructors, destructor, private_methods


def parse_attributes(class_value, doxygen_index):
    attributes = {}
    private_attributes = {}
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
            attribute_type = parse_real_type(xml_attribute, doxygen_index)
            attribute_desc = get_content(xml_attribute.find("briefdescription"))
            initializer = get_content_if(xml_attribute.find("initializer"))
            qualifiers = QualifiersModel(static=is_static)
            flags = parse_obidog_flags(xml_attribute)
            templated = False
            visibility = ItemVisibility(xml_attribute.attrib["prot"])
            attribute_dest = attributes
            if visibility != ItemVisibility.Public:
                attribute_dest = private_attributes
            if xml_attribute.find("templateparamlist") is not None:
                templated = True
            definition = get_content(xml_attribute.find("definition"))
            identifier = parse_definition(definition)[1]
            if " " in identifier:
                identifier = identifier.split(" ")[0]
            namespace = "::".join(identifier.split("::")[:-2])
            if not templated:
                attribute_dest[attribute_name] = AttributeModel(
                    name=attribute_name,
                    namespace=namespace,
                    type=attribute_type,
                    qualifiers=qualifiers,
                    initializer=initializer,
                    description=attribute_desc,
                    flags=flags,
                    location=parse_doxygen_location(xml_attribute),
                    visibility=visibility,
                )

    return attributes, private_attributes


def is_class_non_copyable(class_model: ClassModel):
    for constructor in class_model.constructors:
        if len(constructor.parameters) == 1 and constructor.deleted:
            parsed_type = parse_cpp_type(constructor.parameters[0].type)
            class_fqn = make_fqn(name=class_model.name, namespace=class_model.namespace)
            if parsed_type.qualifiers.is_const_ref() and parsed_type.type == class_fqn:
                return True
    return False


def parse_class_from_xml(class_value, doxygen_index) -> ClassModel:
    nobind = False
    class_name = extract_xml_value(class_value, "compoundname")
    namespace_name, class_name = (
        "::".join(class_name.split("::")[:-1:]),
        class_name.split("::")[-1],
    )
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
            # TODO: resolve with refid first (for inner types)
            bases.append(
                rebuild_incomplete_type(
                    get_content(base).strip(),
                    f"{namespace_name}::{class_name}",
                    doxygen_index,
                )
            )

    description = extract_xml_value(class_value, "briefdescription/para")

    methods, constructors, destructor, private_methods = parse_methods(
        class_name, class_value, doxygen_index
    )
    attributes, private_attributes = parse_attributes(class_value, doxygen_index)
    for attribute in list(attributes.values()) + list(private_attributes.values()):
        attribute.from_class = class_name
    flags = parse_obidog_flags(
        class_value, symbol_name="::".join([namespace_name, class_name])
    )

    templated = False
    if class_value.xpath("templateparamlist"):
        templated = True
        # Ignore template classes without template hints
        if not flags.template_hints:
            nobind = True

    flags.nobind = flags.nobind or nobind

    CONFLICTS.append(class_name, class_value)
    class_model = ClassModel(
        name=class_name,
        namespace=namespace_name,
        abstract=abstract,
        bases=bases,
        attributes=attributes,
        constructors=constructors,
        destructor=destructor,
        methods=methods,
        private_methods=private_methods,
        private_attributes=private_attributes,
        flags=flags,
        template=templated,
        description=description,
        location=parse_doxygen_location(class_value),
    )
    if is_class_non_copyable(class_model):
        class_model.flags.meta.add(MetaTag.NonCopyable.value)
    return class_model
