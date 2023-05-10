import os

from obidog.config import PATH_TO_OBENGINE
from obidog.models.globals import GlobalModel
from obidog.parsers.obidog_parser import get_cpp_element_obidog_flags
from obidog.parsers.location_parser import parse_doxygen_location
from obidog.parsers.type_parser import parse_real_type
from obidog.parsers.utils.doxygen_utils import doxygen_id_to_cpp_id
from obidog.parsers.utils.xml_utils import get_content, get_content_if


# BUG: https://github.com/doxygen/doxygen/issues/6319
def parse_global_from_xml(xml_global, doxygen_index):
    global_id = doxygen_id_to_cpp_id(xml_global.attrib["id"])
    description = get_content(xml_global.find("detaileddescription"))
    if not description:
        description = get_content(xml_global.find("briefdescription"))
    flags = get_cpp_element_obidog_flags(global_id)
    return GlobalModel(
        id=global_id,
        name=get_content(xml_global.find("name")),
        definition=get_content(xml_global.find("definition")),
        type=parse_real_type(xml_global, doxygen_index),
        initializer=get_content_if(xml_global.find("initializer")),
        flags=flags,
        location=parse_doxygen_location(xml_global),
        description=description,
    )
