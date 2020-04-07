from collections import namedtuple
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from datetime import datetime
from fxqu4nt.market.constant import PriceType
Attr = namedtuple("Attr", field_names=["name", "value"])

PRICE_TYPES = [PriceType.Ask.name, PriceType.Bid.name, "Both"]

class DefaultSettings:
    def __init__(self, startDate=None, priceType="Ask"):
        self.attrs = {}
        self.startDate = startDate
        self.priceType = priceType

    @property
    def startDate(self):
        return self.attrs["startDate"].value

    @property
    def priceType(self):
        return self.attrs["priceType"].value

    @startDate.setter
    def startDate(self, sd):
        self.attrs["startDate"] = Attr(name="Start Date", value=sd)

    @priceType.setter
    def priceType(self, pt):
        self.attrs["priceType"] = Attr(name="Price Type", value=pt)

    def setAttr(self, key, value, name):
        self.attrs[key] = Attr(name=name, value=value)


class TickBarSettings(DefaultSettings):
    def __init__(self, startDate=None, stepSize=50):
        DefaultSettings.__init__(self, startDate=startDate)
        self.stepSize = stepSize

    @property
    def stepSize(self):
        return self.attrs["stepSize"].value

    @stepSize.setter
    def stepSize(self, s):
        self.attrs["stepSize"] = Attr(name="Step Size", value=s)


def createSettingsBox(settings: DefaultSettings):
    layout = QFormLayout()
    widgetDict = dict()

    for k, v in settings.attrs.items():
        if k == "priceType":

            continue
        if isinstance(v.value, int) \
            or isinstance(v.value, float) \
            or isinstance(v.value, str) \
            or isinstance(v.value, datetime):
            value = v.value
            if isinstance(value, datetime):
                value = value.strftime('%Y-%m-%dT%H:%M:%S')
            editWidget = QLineEdit(str(value))
            layout.addRow(QLabel(v.name+":"), editWidget)
            widgetDict[k] = editWidget

    return layout, widgetDict