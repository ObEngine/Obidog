import subprocess
import os

from obidog.config import PATH_TO_OBENGINE
from obidog.logger import log

CLANG_FORMAT_PATH = os.environ.get("CLANG_FORMAT_PATH", "clang-format")


def _check_clang_format():
    try:
        with subprocess.Popen(
            [CLANG_FORMAT_PATH, "--version"], stdout=subprocess.PIPE
        ) as clang_format_exec:
            version = clang_format_exec.stdout.read().decode("utf-8").strip()
            try:
                version = version.split()[2]
                if int(version.split(".")[0]) >= 10:
                    return True
                else:
                    return False
            except Exception as e:
                log.warning(
                    f"unable to use clang-format at '{CLANG_FORMAT_PATH}' : {e}"
                )
                return False
    except FileNotFoundError as e:
        log.warning(f"unable to find clang-format at '{CLANG_FORMAT_PATH}' : {e}")
        return False


def clang_format_files(file_list):
    if CLANG_FORMAT_PATH is not None:
        for path in file_list:
            p = subprocess.Popen(
                [CLANG_FORMAT_PATH, "-i", "-style=file", path], cwd=PATH_TO_OBENGINE
            )
            p.wait()
        return True
    log.warning("clang-format not found, could not format files")
    return False


if not _check_clang_format():
    CLANG_FORMAT_PATH = None
