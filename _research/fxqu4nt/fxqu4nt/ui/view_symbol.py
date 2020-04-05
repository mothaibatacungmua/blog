from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from pandas import Timestamp
from datetime import datetime
from fxqu4nt.market.kdb import get_db
from fxqu4nt.market.symbol import Symbol
from fxqu4nt.ui.view.settings import createSettingsBox, TickBarSettings


class ViewSymbol(QDialog):
    def __init__(self, symbol:[str, Symbol], parent=None):
        self.parent = parent
        QDialog.__init__(self, parent=parent)
        self.setWindowModality(Qt.NonModal)
        self.symbol = symbol
        self.createLayout()
        self.kdb = get_db()
        self.createDefaultSettings()

    def createDefaultSettings(self):
        pdFirstDateTime: Timestamp = self.kdb.first_quote_date(self.symbol)
        firstDateTime = pdFirstDateTime.to_pydatetime()
        firstDateTime = datetime(year=firstDateTime.year,
                                 month=firstDateTime.month,
                                 day=firstDateTime.day)
        self.defaultSettings = TickBarSettings(startDate=firstDateTime, stepSize=50)

    @property
    def symbolName(self):
        return self.symbol.name if isinstance(self.symbol, Symbol) else self.symbol

    def createLayout(self):
        self.setWindowTitle("View %s" % self.symbolName)
        layout = QHBoxLayout()

        # Create setting group box
        settingGroup = QGroupBox("Settings")
        settingVBoxLayout = QVBoxLayout()
        symbolName = self.symbol.name if isinstance(self.symbol, Symbol) else self.symbol
        symblLbl = QLabel("Symbol: " + symbolName)
        settingVBoxLayout.addWidget(symblLbl)
        settingGroup.setLayout(settingVBoxLayout)

        layout.addWidget(settingGroup)
        self.layout = layout
        self.setLayout(layout)

