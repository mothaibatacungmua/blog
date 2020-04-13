from collections import OrderedDict
import math

class Symbol(object):
    def __init__(
            self, name: str = None,
            point: float = 0.00001,
            min_vol: float = 0.01,
            max_vol: float = 0.01,
            vol_step: float = 0.01):
        self.name = name
        self.point = point
        self.min_vol = min_vol
        self.max_vol = max_vol
        self.vol_step = vol_step

    def to_dict(self):
        return OrderedDict(
            name=self.name,
            point=self.point,
            min_vol=self.min_vol,
            max_vol=self.max_vol,
            vol_step=self.vol_step
        )

    @property
    def digits(self):
        return int(round(math.log10(1 / self.point)))

    @classmethod
    def from_dict(self, d):
        return Symbol(
            name=d["name"],
            point=d["point"],
            min_vol=d["min_vol"],
            max_vol=d["max_vol"],
            vol_step=d["vol_step"]
        )

    def __repr__(self):
        return "[name={name}, point={point}, min_vol={min_vol}, max_vol={max_vol}, vol_step={vol_step}]"\
                .format(name=self.name,
                        point=self.point,
                        min_vol=self.min_vol,
                        max_vol=self.max_vol,
                        vol_step=self.vol_step)

    def __str__(self):
        return self.__repr__()