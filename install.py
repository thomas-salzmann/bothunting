"""
Implements make target 'install'.
"""

import pathlib
import subprocess
import sys
from typing import Union

sys.path += [
    "./bothunting/",
    "./bothunting/utils",
]
from bothunting import definitions
from bothunting.utils import fileutil
from bothunting.utils import osutil
from bothunting.utils import pathutil


def gen_vscode_settings(prj_root: pathlib.Path, platform_):
    vscode_dir = prj_root / ".vscode"
    if not pathutil.is_dir(vscode_dir):
        osutil.mkdir(vscode_dir)

    home_dir = definitions.get_home_directory()
    virtualenvs_dir = None
    bin_dir = None
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
        '    "python.pythonPath": "' + path_python3 + '",',
        '    "python.formatting.provider": "black",',
        '    "python.formatting.blackArgs": [',
        '        "--line-length",',
        '        "80",',
        "    ],",
        '    "editor.formatOnSave": true,',
        '    "workbench.editor.enablePreview": false,',
        '    "files.watcherExclude": {',
        '        "**' + sep + ".git" + sep + "objects" + sep + '**": true,',
        '        "**'
        + sep
        + ".git"
        + sep
        + "subtree-cache"
        + sep
        + '**": true,',
        '        "**' + sep + "node_modules" + sep + "*" + sep + '**": true',
        "    },",
        "}",
    )

    path_vscode_file = vscode_dir / "settings.json"
    fileutil.writelines(path_vscode_file, lines, append_newlines=True)


def set_environment_variables(prj_root: pathlib.Path, platform_: str) -> None:
    if platform_ == ("linux", "mac"):
        # Update ~/.bashrc file.
        home_dir = definitions.get_home_directory()
        path_env_var = osutil.getenv("PATH")
        osutil.setenv(
            "PATH", str(home_dir / ".local" / "bin") + ":" + path_env_var
        )

        bashrc_path = home_dir / ".bashrc"
        bashrc_lines = fileutil.readlines(bashrc_path, rstrip=True)
        first_install = True
        if "### Bothunting AI definitions" in bashrc_lines:
            first_install = False

        if first_install:
            # Append definition of environment variables to ~/.bashrc
            bashrc_lines.append("\n### Bothunting AI definitions")
            bashrc_lines.append("export PATH=" + path_env_var)
            bashrc_lines.append("export TECHLABS_PRJ_ROOT_5=" + str(prj_root))
            bashrc_lines.append(
                "export PYTHONPATH="
                + str(prj_root)
                + ":"
                + osutil.getenv("PYTHONPATH")
            )
    elif platform_ == "windows":
        proc = subprocess.Popen(
            "python -m site --user-site".split(), stdout=subprocess.PIPE
        )
        output, _ = proc.communicate()
        python_user_site_pkg = pathlib.Path(output.decode("utf-8").strip())
        python_user_scripts_dir = (
            pathutil.parent(python_user_site_pkg) / "Scripts"
        )

        print(
            "Before proceeding, please extend the following environment variables by the mentioned values:\n"
        )

        path_env_var = osutil.getenv("PATH")
        osutil.setenv("PATH", str(python_user_scripts_dir) + ";" + path_env_var)

        print("PATH: " + str(python_user_scripts_dir))
        print("TECHLABS_PRJ_ROOT_5: " + str(prj_root))
        print("PYTHONPATH: " + str(prj_root))

        while True:
            answer = input("Have you set the environment variables ? [Y/N]")

            if answer == "Y":
                break
            else:
                print("Please set the environment variables before proceeding.")


def install_dependencies(prj_root: pathlib.Path, platform_: str):
    if platform_ == "windows":
        commands = (
            "python -m pip install pipenv --user",
            "pipenv install --dev",
            "pipenv run pip install black",
            "pipenv run pip install tensorflow==2.1.0",
        )
    elif platform_ in ("linux", "mac"):
        commands = (
            "python3 -m pip install pipenv --user",
            "pipenv install --dev",
            "pipenv run pip install black",
            "pipenv run pip install tensorflow==2.1.0",
        )

    for command in commands:
        subprocess.run(command.split())


def create_out_dir(prj_root: pathlib.Path) -> None:
    out_dir = prj_root / "out_dir"
    if not pathutil.is_dir(out_dir):
        osutil.mkdir(out_dir)


def run(
    prj_root: Union[str, pathlib.Path],
    platform_: str,
):
    prj_root = pathutil.str_to_path(prj_root)

    set_environment_variables(prj_root, platform_)
    install_dependencies(prj_root, platform_)
    gen_vscode_settings(prj_root, platform_)
    create_out_dir(prj_root)

    return 0


def main():
    prj_root = definitions.get_prj_root()
    platform_ = definitions.get_platform()
    exit_code = run(prj_root, platform_)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
