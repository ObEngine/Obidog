import os
from obidog.parsers.utils.xml_utils import get_content, get_content_if
from obidog.parsers.obidog_parser import parse_obidog_flags, CONFLICTS
from obidog.config import PATH_TO_OBENGINE

# BUG: https://github.com/doxygen/doxygen/issues/6319
def parse_global_from_xml(xml_global):
    description = get_content(xml_global.find("detaileddescription"))
    if not description:
        description = get_content(xml_global.find("briefdescription"))
    location = xml_global.find("location").attrib["file"]
    CONFLICTS.append(get_content(xml_global.find("name")), xml_global)
    return {
        "name": get_content(xml_global.find("name")),
        "definition": get_content(xml_global.find("definition")),
        "type": get_content(xml_global.find("type")),
        "initializer": get_content_if(xml_global.find("initializer")),
        "location": os.path.relpath(
                os.path.normpath(location),
                os.path.normpath(PATH_TO_OBENGINE)),
        "description": description
    }