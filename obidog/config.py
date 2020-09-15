import os

PATH_TO_OBENGINE = os.environ.get("OBENGINE_GIT_DIRECTORY", None)
BINDINGS_SOURCES_LOCATION = "src/Core"
BINDINGS_HEADERS_LOCATION = "include/Core"
SOURCE_DIRECTORIES = [
    # {"path": "src/Core", "namespace": "obe"},
    {"path": "include/Core", "namespace": "obe"},
    {"path": "extlibs/vili/include", "namespace": "vili"},
]
BINDINGS_CONFIG_FILE = "Bindings/Config.hpp"
OBENGINE_GIT_URL = os.environ.get(
    "OBENGINE_GIT_URL", "https://github.com/Sygmei/ObEngine"
)
OBENGINE_GIT_SSH = os.environ.get("OBENGINE_GIT_SSH", "git@github.com:Sygmei/ObEngine")


def set_obengine_git_directory(directory):
    global PATH_TO_OBENGINE
    os.environ["OBENGINE_GIT_DIRECTORY"] = directory
    PATH_TO_OBENGINE = directory
    return PATH_TO_OBENGINE