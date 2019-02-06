import os
import tempfile

import git

OBENGINE_GIT_URL = os.environ.get(
    "OBENGINE_GIT_URL",
    "https://github.com/Sygmei/ObEngine")


def clone_obengine_repo():
    path = tempfile.mkdtemp()
    repo = git.Repo.clone_from(
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
