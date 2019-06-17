import os
import tempfile

import git

from obeldog.exceptions import InvalidObEngineGitRepositoryException
from obeldog.logger import log

OBENGINE_GIT_URL = os.environ.get(
    "OBENGINE_GIT_URL",
    "https://github.com/Sygmei/ObEngine")

def check_git_directory():
    if "OBENGINE_GIT_DIRECTORY" in os.environ:
        path_to_obengine = os.environ["OBENGINE_GIT_DIRECTORY"]
        log.debug(f"Found existing ÖbEngine repository in {path_to_obengine}")
    else:
        log.debug("Cloning ÖbEngine repository...")
        path_to_obengine = clone_obengine_repo()
    log.debug("Checking ÖbEngine repository validity...")
    if not check_obengine_repo(path_to_obengine):
        raise InvalidObEngineGitRepositoryException(path_to_obengine)
    log.info(f"Using ÖbEngine repository in {path_to_obengine}")
    return path_to_obengine

def clone_obengine_repo():
    path = tempfile.mkdtemp()
    git.Repo.clone_from(
        OBENGINE_GIT_URL,
        path,
        branch='master'
    )
    return path


def check_obengine_repo(git_dir):
    try:
        repo = git.Repo(git_dir)
    except:
        return False
    return OBENGINE_GIT_URL in repo.remote().urls
