import os

PATH_TO_OBENGINE = os.environ.get("OBENGINE_GIT_DIRECTORY", None)
BINDINGS_SOURCES_LOCATION = "src/Core"
LOCATIONS = {
    "Core": {"headers": "include/Core/Bindings", "sources": "src/Core/Bindings"},
    "Dev": {"headers": "include/Dev/Bindings", "sources": "src/Dev/Bindings"},
}
SOURCE_DIRECTORIES = [
    # {"path": "src/Core", "namespace": "obe"},
    # {
    #     "path": "include/Core",
    #     "namespace": "obe",
    #     "exclude_paths": ["Bindings/**/**"],
    #     "output_location": "Core",
    #     "structure_policy": "namespaces",
    # },
    {
        "path": "include/Dev",
        "namespace": None,
        "exclude_paths": ["Bindings/**/**"],
        "output_location": "Dev",
        "structure_policy": "namespaces",
    },
    # {
    #     "path": "extlibs/vili/include",
    #     "namespace": "vili",
    #     "output_location": "Core",
    #     "structury_policy": "namespaces",
    # },
    {
        "path": "extlibs/tgui/include",
        "namespace": "tgui",
        "exclude_paths": ["TGUI/Backends/**", "TGUI/extlibs/**"],
        "exclude_symbols": [
            "tgui::dev",
            "tgui::utf",
            "tgui::keyboard",
            "tgui::priv",
            "tgui::bind_functions",
        ],
        "output_location": "Dev",
        "structure_policy": "classes",
    },
]
SOURCE_DIRECTORIES_BY_OUTPUT = {
    location: [
        source["namespace"]
        for source in SOURCE_DIRECTORIES
        if source["output_location"] == location and source["namespace"] is not None
    ]
    for location in LOCATIONS
}

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
