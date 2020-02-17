import os

def strip_include(path):
    for strip_path in ["include/Core", "include/Dev", "include/Player"]:
        if os.path.commonprefix([strip_path, path]):
            path = os.path.relpath(path, strip_path)
    return path