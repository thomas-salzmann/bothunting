import pathlib
import platform


def get_prj_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent.parent

def get_root_python_package():
    return get_prj_root() / "bothunting"

def get_platform() -> str:
    platform_ = platform.system().lower()
    if platform_ == "darwin":
        platform_ = "mac"
    return platform_


def get_home_directory():
    return pathlib.Path.home()


def sep():
    platform_ = get_platform()
    if platform_ == "windows":
        sep = "\\"
    elif platform_ in ("linux", "darwin"):
        sep = "/"
    return sep
