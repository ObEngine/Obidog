import os
import shutil
import subprocess
import tempfile


def build_doxygen_documentation(source_path):
    path = tempfile.mkdtemp()
    src_directories = [os.path.join(source_path, directory) for directory in [
        "include",
        "extlibs/vili/include/vili",
    ]]
    with open("Doxyfile", "r") as src_doxyfile:
        with open(os.path.join(path, "Doxyfile"), "w") as dst_doxyfile:
            dst_doxyfile.write(
                src_doxyfile.read().replace(
                    "{{input_directories}}",
                    (" \\\n" + " " * 25).join(src_directories)
                )
            )
    with open(os.path.join(path, "out.log"), "w") as log:
        subprocess.run(
            ["doxygen", "Doxyfile"],
            cwd=path,
            stdout=log,
            stderr=log)
    return path