import os

from obidog.config import PATH_TO_OBENGINE
from obidog.models.location import Location


def parse_doxygen_location(element):
    location_node = element.find("location")
    file_location = location_node.attrib["file"]

    file_location = os.path.relpath(
        os.path.normpath(file_location), os.path.normpath(PATH_TO_OBENGINE)
    ).replace(os.path.sep, "/")
    return Location(
        file=file_location,
        line=int(location_node.attrib["line"]),
        column=int(location_node.attrib["column"]),
    )
