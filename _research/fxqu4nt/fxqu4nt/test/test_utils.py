import os


def get_test_dir():
    dirname = os.path.dirname(os.path.realpath(__file__))
    return dirname


def get_test_data():
    return os.path.join(get_test_dir(), "data")