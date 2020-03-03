import os
import yaml

PACKAGE_NAME = "FxQu4nt"
VERSION = "0.0.1"

gmcnf = None

def get_project_dir():
    return os.path.dirname(__file__)


def get_appdata_dir():
    return os.path.join(os.path.expandvars("%LOCALAPPDATA%"), "fxqu4nt")


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