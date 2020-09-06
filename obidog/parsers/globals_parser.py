import os

from obidog.config import PATH_TO_OBENGINE
from obidog.models.globals import GlobalModel
from obidog.parsers.obidog_parser import CONFLICTS, parse_obidog_flags
from obidog.parsers.location_parser import parse_doxygen_location
from obidog.parsers.utils.xml_utils import get_content, get_content_if


# BUG: https://github.com/doxygen/doxygen/issues/6319
def parse_global_from_xml(xml_global):
    description = get_content(xml_global.find("detaileddescription"))
    if not description:
        description = get_content(xml_global.find("briefdescription"))
    CONFLICTS.append(get_content(xml_global.find("name")), xml_global)
    return GlobalModel(
        name=get_content(xml_global.find("name")),
        definition=get_content(xml_global.find("definition")),
        type=get_content(xml_global.find("type")),
        initializer=get_content_if(xml_global.find("initializer")),
        location=parse_doxygen_location(xml_global),
        description=description,
    )
