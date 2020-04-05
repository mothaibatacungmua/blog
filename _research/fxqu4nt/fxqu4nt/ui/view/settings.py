from collections import namedtuple
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

Attr = namedtuple("Attr", field_names=["name", "value"])


class DefaultSettings:
    def __init__(self, startDate=None):
        self.attrs = {}
        self.startDate = startDate

    @property
    def startDate(self):
        return self.attrs["startDate"].value

    @startDate.setter
    def startDate(self, sd):
        self.attrs["startDate"] = Attr(name="Start Date", value=sd)

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
        if isinstance(v.value, int) \
            or isinstance(v.value, float) \
            or isinstance(v.value, str):
            editWidget = QLineEdit(str(v.value))
            layout.addRow(QLabel(v.name), editWidget)
            widgetDict[k] = editWidget

    return layout