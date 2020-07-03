import os

PATH_TO_OBENGINE = os.environ.get("OBENGINE_GIT_DIRECTORY", None)
SOURCE_DIRECTORIES = [
    {"path": "include/Core", "namespace": "obe"},
    {"path": "extlibs/vili/include", "namespace": "vili"}
]
BINDINGS_CONFIG_FILE = "Bindings/Config.hpp"