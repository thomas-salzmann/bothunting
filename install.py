"""
Implements make target 'install'.
"""

from bothunting.utils import pathutil
from bothunting.utils import osutil
from bothunting.utils import fileutil
from bothunting import definitions
import pathlib
import subprocess
import sys
from typing import Union

sys.path += [
    "./bothunting/",
    "./bothunting/utils",
]


def gen_vscode_settings(prj_root: pathlib.Path, platform_):
    vscode_dir = prj_root / ".vscode"
    if not pathutil.is_dir(vscode_dir):
        osutil.mkdir(vscode_dir)

    home_dir = definitions.get_home_directory()
    if platform_ in ("linux", "mac"):
        virtualenvs_dir = home_dir / ".local" / "share" / "virtualenvs"
        bin_dir = "bin"
    elif platform_ == "windows":
        virtualenvs_dir = home_dir / ".virtualenvs"
        bin_dir = "Scripts"
    _, dirs = pathutil.walk(virtualenvs_dir, depth=1)
    project_dir = None
    for x in dirs:
        if pathutil.basename(
            definitions.get_root_python_package()
        ) in pathutil.basename(x):
            project_dir = x
            break

    path_python3 = str(project_dir / bin_dir)
    sep = definitions.sep()
    if platform_ == "windows":
        path_python3 = path_python3.replace("\\", "\\\\")
        sep = 2 * sep

    lines = (
        "{",
        '    "editor.defaultFormatter": "ms-python.autopep8",',
        '    "editor.formatOnSave": true,',
        "}",
    )

    path_vscode_file = vscode_dir / "settings.json"
    fileutil.writelines(path_vscode_file, lines, append_newlines=True)


def install_dependencies(prj_root: pathlib.Path, platform_: str):
    if platform_ == "indows":
        commands = (
            "python -m pip install pipenv --user",
            "pipenv install --dev",
            "pipenv run pip install black",
        )
    elif platform_ in ("linux", "mac"):
        commands = (
            "python3 -m pip install pipenv --user",
            "pipenv install --dev",
            "pipenv run pip install black",
        )

    for command in commands:
        subprocess.run(command.split())


def run(
    prj_root: Union[str, pathlib.Path],
    platform_: str,
):
    prj_root = pathutil.str_to_path(prj_root)

    install_dependencies(prj_root, platform_)
    gen_vscode_settings(prj_root, platform_)

    return 0


def main():
    prj_root = definitions.get_prj_root()
    platform_ = definitions.get_platform()
    exit_code = run(prj_root, platform_)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
