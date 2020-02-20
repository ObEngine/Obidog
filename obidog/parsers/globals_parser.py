from obidog.parsers.utils.xml_utils import get_content, get_content_if

# BUG: https://github.com/doxygen/doxygen/issues/6319
def parse_global_from_xml(xml_global):
    description = get_content(xml_global.find("detaileddescription"))
    if not description:
        description = get_content(xml_global.find("briefdescription"))
    return {
        "name": get_content(xml_global.find("name")),
        "definition": get_content(xml_global.find("definition")),
        "type": get_content(xml_global.find("type")),
        "initializer": get_content_if(xml_global.find("initializer")),
        "location": xml_global.find("location").attrib["file"],
        "description": description
    }