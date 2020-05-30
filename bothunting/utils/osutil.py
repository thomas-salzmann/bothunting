import os
import pathlib
import shutil

from typing import Any, Union


def mkdir(path: Union[str, pathlib.Path], parents: bool = True, exist_ok: bool = False):
    """ Create a directory """
    pathlib.Path(path).mkdir(parents=parents, exist_ok=exist_ok)


def getenv(name: str) -> str:
    """ Retrieve environment variable. """
    return os.getenv(name)


def setenv(name: str, value: Any) -> None:
    """ Set environment variable. """
    os.environ[name] = value
