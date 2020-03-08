from datetime import datetime

JAN_1_2000 = datetime(year=2000, month=1, day=1, hour=0, second=0, microsecond=0)


def normalize_path(path: str):
    return path.replace("\\", "/")


def serialize_datetime_fn(dt: float):
    #TODO
    pass


def serialize_symbol_name(name):
    return name.decode("utf-8")