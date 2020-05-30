import pathlib
from typing import List, Union

from bothunting.utils import pathutil


def readlines(
    path: Union[str, pathlib.Path],
    encoding="utf-8",
    lstrip=False,
    rstrip=False,
) -> List[str]:
    """ Retrieve lines from file. """
    with open(path, "r", encoding=encoding) as f:
        lines = f.readlines()
    if lstrip:
        lines = [x.lstrip() for x in lines]
    if rstrip:
        lines = [x.rstrip() for x in lines]
    return lines


def writelines(
    path: Union[str, pathlib.Path],
    lines: List[str],
    append_newlines=False,
    append_data=False
) -> None:
    """ Write lines to file. """
    if append_newlines:
        lines = [x + "\n" for x in lines]

    mode = "w"
    if append_data:
        mode = "a"
    with open(path, mode=mode) as f:
        f.writelines(lines)
