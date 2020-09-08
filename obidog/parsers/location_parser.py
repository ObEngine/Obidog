import os

from obidog.config import PATH_TO_OBENGINE
from obidog.models.location import Location


def parse_doxygen_location(element):
    location_node = element.find("location")
    has_body = "bodyfile" in location_node.attrib
    file_location = (
        location_node.attrib["bodyfile"] if has_body else location_node.attrib["file"]
    )

    file_location = os.path.relpath(
        os.path.normpath(file_location), os.path.normpath(PATH_TO_OBENGINE)
    ).replace(os.path.sep, "/")
    line = (
        int(location_node.attrib["bodystart"])
        if has_body
        else int(location_node.attrib["line"])
    )
    return Location(
        file=file_location,
        line=line,
        column=0 if has_body else int(location_node.attrib["column"]),
    )
