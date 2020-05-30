import pathlib

from typing import List, Union, Tuple


def path_to_str(path: Union[str, pathlib.Path]) -> str:
    """ Convert pathlib.Path object to string. """
    return str(path)


def str_to_path(path: Union[str, pathlib.Path]) -> bool:
    """ Convert string object to pathlib.Path """
    return pathlib.Path(path)


def is_file(path: Union[str, pathlib.Path]) -> bool:
    """ Check if file system path points to a file. """
    path = str_to_path(path)
    return path.is_file()


def basename(path: Union[str, pathlib.Path]) -> str:
    """ Retrieve basename - final path component. """
    path = str_to_path(path)
    return path.name


def filename(path: Union[str, pathlib.Path], file_extension=True) -> str:
    """ Retrieve filename. """
    path = str_to_path(path)
    if is_file(path):
        if file_extension:
            return path.name
        return path.stem
    return ""


def suffix(path: Union[str, pathlib.Path]) -> str:
    """ Retrieve suffix of path. """
    path = str_to_path(path)
    return path.suffix


def parent(path: Union[str, pathlib.Path]) -> str:
    """ Retrieve parent directory. """
    path = str_to_path(path)
    return path.parent


def is_dir(path: Union[str, pathlib.Path]) -> bool:
    """ Check if file system path points to a directory. """
    path = str_to_path(path)
    return path.is_dir()


def walk(
    root: Union[str, pathlib.Path], depth: int = -1
) -> Tuple[List[pathlib.Path], List[pathlib.Path], List[pathlib.Path]]:
    """ Traverse directory tree recursively and return files and directories. """
    root = str_to_path(root)

    files = []
    dirs = []
    dirs_new = []

    if not is_dir(root):
        return [], [], []
    dirs.append(root)
    dirs_new.append(root)
    while dirs_new:
        dir_ = dirs_new.pop(0)
        if depth != -1:
            relpath = dir_.relative_to(root)
            parts_ = relpath.parts
            if len(parts_) >= depth:
                break

        for x in dir_.iterdir():
            if is_file(x):
                files.append(x)
            elif is_dir(x):
                dirs.append(x)
                dirs_new.append(x)
    return files, dirs
