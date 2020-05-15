import os
import yaml
import platform
from fxqu4nt.utils.common import normalize_path


gmcnf = None


def get_project_dir():
    return os.path.dirname(__file__)


def get_appdata_dir():
    if platform.system() == "Windows":
        return os.path.join(os.path.expandvars("%LOCALAPPDATA%"), "fxqu4nt")

    if platform.system() == "Darwin" or platform.system() == "Linux":
        return os.path.join(os.path.expandvars("$HOME"), ".fxqu4nt")


def get_q_dir():
    return os.path.join(get_project_dir(), "q")


def get_all_q_utils_paths():
    ret = []
    utils_dir = os.path.join(get_q_dir(), "utils")
    for f in os.listdir(utils_dir):
        if f.endswith(".q"):
            ret.append(normalize_path(os.path.join(utils_dir, f)))
    return ret


def get_all_q_script_paths():
    ret = []
    for f in os.listdir(get_q_dir()):
        if f.endswith(".q"):
            ret.append(normalize_path(os.path.join(get_q_dir(), f)))
    return ret


def get_mcnf():
    global gmcnf
    if gmcnf is None:
        fpath = os.path.join(get_appdata_dir(), "mcnf.yaml")
        if os.path.exists(fpath):
            with open(fpath) as fobj:
                gmcnf = yaml.load(fobj)
            return gmcnf
        else:
            return None
    else:
        return gmcnf


def save_mcnf(cnf):
    global gmcnf
    appdata_dir = get_appdata_dir()
    if not os.path.exists(appdata_dir):
        os.makedirs(appdata_dir)
    fpath = os.path.join(get_appdata_dir(), "mcnf.yaml")
    with open(fpath, "w") as fobj:
        yaml.dump(cnf, fobj)
        gmcnf = fobj