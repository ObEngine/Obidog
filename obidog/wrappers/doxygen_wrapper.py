import os
import subprocess
import tempfile

import semver

from obidog.config import SOURCE_DIRECTORIES
from obidog.logger import log

DOXYGEN_PATH = os.environ.get("DOXYGEN_PATH", "doxygen")


def _check_doxygen():
    try:
        with subprocess.Popen(
            [DOXYGEN_PATH, "--version"], stdout=subprocess.PIPE
        ) as doxygen_exec:
            version = doxygen_exec.stdout.read().decode("utf-8").strip()
            try:
                version = version.split()[0]
                version = semver.VersionInfo.parse(version)
                if version >= semver.VersionInfo(major=1, minor=8, patch=18):
                    return True
                else:
                    return False
            except:
                return False
    except FileNotFoundError as e:
        log.warning(f"doxygen not found at '{DOXYGEN_PATH}' : {e}")
        return False


def build_doxygen_documentation(source_path):
    path = tempfile.mkdtemp()
    src_directories = [
        os.path.join(source_path, directory)
        for directory in [item["path"] for item in SOURCE_DIRECTORIES]
    ]
    exclude_directories = [
        os.path.join(source_path, source["path"], exclude).replace("\\", "/")
        for source in SOURCE_DIRECTORIES
        if "exclude_paths" in source
        for exclude in source["exclude_paths"]
    ]
    exclude_symbols = [
        excluded_symbol
        for source in SOURCE_DIRECTORIES
        if "exclude_symbols" in source
        for excluded_symbol in source["exclude_symbols"]
    ]
    with open("Doxyfile", "r") as src_doxyfile:
        doxyfile_content = src_doxyfile.read()
        with open(os.path.join(path, "Doxyfile"), "w") as dst_doxyfile:
            dst_doxyfile.write(
                doxyfile_content.replace(
                    "{{input_directories}}", (" \\\n" + " " * 25).join(src_directories)
                )
                .replace(
                    "{{exclude_patterns}}",
                    (" \\\n" + " " * 25).join(exclude_directories),
                )
                .replace(
                    "{{exclude_symbols}}", (" \\\n" + " " * 25).join(exclude_symbols)
                )
            )
    with open(os.path.join(path, "out.log"), "w") as logger:
        subprocess.run(
            [DOXYGEN_PATH, "Doxyfile"], cwd=path, stdout=logger, stderr=logger
        )
    return path


if not _check_doxygen():
    raise RuntimeError("Doxygen (>= 1.8.18) not found")
