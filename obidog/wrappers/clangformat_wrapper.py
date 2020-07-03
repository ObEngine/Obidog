import subprocess
import os

from obidog.config import PATH_TO_OBENGINE

CLANG_FORMAT_PATH = os.environ.get("CLANG_FORMAT_PATH", "clang-format")

def clang_format_files(file_list):
    for path in file_list:
        p = subprocess.Popen(
            [CLANG_FORMAT_PATH, "-i", "-style=file", path],
            cwd=PATH_TO_OBENGINE
        )
        p.wait()