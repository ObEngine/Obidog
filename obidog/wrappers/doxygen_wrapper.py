import os
import shutil
import subprocess
import tempfile

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
                version = version.split()[0].split(".")
                if int(version[0]) >= 1 and int(version[1]) >= 8 and int(version[2]) >= 18:
                    return True
                else:
                    return False
            except:
                return False
    except FileNotFoundError as e:
        return False

def build_doxygen_documentation(source_path):
    path = tempfile.mkdtemp()
    src_directories = [
        os.path.join(source_path, directory)
        for directory in [item["path"] for item in SOURCE_DIRECTORIES]
    ]
    with open("Doxyfile", "r") as src_doxyfile:
        with open(os.path.join(path, "Doxyfile"), "w") as dst_doxyfile:
            dst_doxyfile.write(
                src_doxyfile.read().replace(
                    "{{input_directories}}", (" \\\n" + " " * 25).join(src_directories)
                )
            )
    with open(os.path.join(path, "out.log"), "w") as logger:
        subprocess.run([DOXYGEN_PATH, "Doxyfile"], cwd=path, stdout=logger, stderr=logger)
    return path


if not _check_doxygen():
    raise RuntimeError(f"Doxygen (>= 1.8.18) not found")