import os
import platform
import numpy as np
from qpython.qtemporal import qtemporal
from qpython import qtype
from datetime import datetime
from fxqu4nt import APP_NAME

JAN_1_2000 = datetime(year=2000, month=1, day=1, hour=0, second=0, microsecond=0)


def normalize_path(path: str):
    return path.replace("\\", "/")


def _serialize_q_datetime(dt: datetime, type="ns"):
    """ Convert python datetime to q datetime

    :param dt: Python datetime input
    :param type: ns = timestamp, D = date, ms = datetime
    :return:
    """
    if type == "ns":
        return qtemporal(np.datetime64(dt), qtype=qtype.QTIMESTAMP)
    elif type == "D":
        return qtemporal(np.datetime64(dt), qtype=qtype.QDATE)
    elif type == "ms":
        return qtemporal(np.datetime64(dt), qtype=qtype.QDATETIME)


sqdt = _serialize_q_datetime


def serialize_symbol_name(name):
    return name.decode("utf-8")


def q_dt_str(dt: datetime):
    return  dt.strftime("%Y.%m.%dT%H:%M:%S.%f")


def get_tmp_dir():
    if platform.system() == "Windows":
        return os.path.join("C:\\Users\\", os.path.expandvars("%USERNAME%"), "AppData\\Local\\Temp\\"+APP_NAME)

    if platform.system() == "Darwin" or platform.system() == "Linux":
        return os.path.join("/tmp/"+APP_NAME)