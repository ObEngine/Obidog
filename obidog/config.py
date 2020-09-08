import os

PATH_TO_OBENGINE = os.environ.get("OBENGINE_GIT_DIRECTORY", None)
SOURCE_DIRECTORIES = [
    {"path": "src/Core", "namespace": "obe"},
    {"path": "include/Core", "namespace": "obe"},
    {"path": "extlibs/vili/include", "namespace": "vili"},
]
BINDINGS_CONFIG_FILE = "Bindings/Config.hpp"


def set_obengine_git_directory(directory):
    global PATH_TO_OBENGINE
    os.environ["OBENGINE_GIT_DIRECTORY"] = directory
    PATH_TO_OBENGINE = directory
    return PATH_TO_OBENGINE