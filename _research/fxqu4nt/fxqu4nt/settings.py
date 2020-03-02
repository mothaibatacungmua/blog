import os
import yaml

PACKAGE_NAME = "FxQu4nt"
VERSION = "0.0.1"

def get_project_dir():
    return os.path.dirname(__file__)


def get_mcnf():
    with open(os.path.join(get_project_dir(), "mcnf.yaml")) as fobj:
        config = yaml.load(fobj)
    return config