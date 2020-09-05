from multiprocessing import Value
import pathlib
import platform


def get_prj_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent.parent


def get_root_python_package() -> pathlib.Path:
    return get_prj_root() / "bothunting"


def get_out_dir() -> pathlib.Path:
    return get_prj_root() / "out"


def get_platform() -> str:
    platform_ = platform.system().lower()
    if platform_ == "darwin":
        platform_ = "mac"
    return platform_


def get_home_directory() -> pathlib.Path:
    return pathlib.Path.home()


def sep() -> str:
    platform_ = get_platform()
    sep = None
    if platform_ == "windows":
        sep = "\\"
    elif platform in ("linux", "mac"):
        sep = "/"
    else:
        raise ValueError("Unknown platform")
    return sep
