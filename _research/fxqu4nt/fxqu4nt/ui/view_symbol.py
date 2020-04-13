from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from copy import deepcopy
from pandas import Timestamp
from datetime import datetime
from datetime import timedelta
import time

from fxqu4nt.market.kdb import get_db
from fxqu4nt.market.symbol import Symbol
from fxqu4nt.market.bar import TickBar
from fxqu4nt.market.constant import PriceType
from fxqu4nt.ui.view.settings import createSettingsBox, TickBarSettings
from fxqu4nt.ui.view.candlestick import CandleSticksWidget

TICK_BAR = "Tick Bar"
TICK_VOLUME_BAR = "Tick Volume Bar"
TIME_BAR = "Time Bar"
BAR_TYPES = [TICK_BAR, TICK_VOLUME_BAR, TIME_BAR]


class ViewSymbol(QDialog):
    def __init__(self, symbol:[str, Symbol], parent=None):
        self.parent = parent
        QDialog.__init__(self, parent=parent)
        self.setWindowModality(Qt.NonModal)
        self.adjustSize()
        self.kdb = get_db()
        self.symbol = symbol
        self.barFeed = TickBar(kdb=self.kdb, symbol=self.symbol)
        self.defaultSettings = self.createDefaultSettings()
        self.currentSettings = deepcopy(self.defaultSettings)
        self.startDate = self.currentSettings.startDate
        self.endDate = self.startDate + timedelta(days=5)

        self.widgetBox = dict()

        desktop = QApplication.desktop()
        res: QRect = desktop.screenGeometry()
        self.desktopWidth = res.getCoords()[2]
        self.desktopHeight = res.getCoords()[3]

        self.adjustedWidth = int(self.desktopWidth * 0.75)
        self.adjustedHeight = int(self.desktopHeight * 0.666)

        self.createLayout()
        self.resize(self.adjustedWidth, self.adjustedHeight)

    def createDefaultSettings(self):
        pdFirstDateTime: Timestamp = self.kdb.first_quote_date(self.symbol)
        firstDateTime = pdFirstDateTime.to_pydatetime()
        firstDateTime = datetime(year=firstDateTime.year,
                                 month=firstDateTime.month,
                                 day=firstDateTime.day)
        return TickBarSettings(startDate=firstDateTime, stepSize=50)

    def getBars(self, sd, ed, barType='tick'):
        bars = []
        if barType == TICK_BAR:
            if self.currentSettings.priceType != "Both":
                bars = self.tickBarGen.fetch(sdt=sd, edt=ed,
                                  price_type=PriceType.from_string(self.currentSettings.priceType),
                                  step_size=self.currentSettings.stepSize,
                                  pandas=False)
                return bars
        return bars

    def leftScrollCallback(self):
        pass

    def rightScrollCallback(self):
        pass

    @property
    def symbolName(self):
        return self.symbol.name if isinstance(self.symbol, Symbol) else self.symbol

    def createLayout(self):
        self.setWindowTitle("View %s" % self.symbolName)
        layout = QHBoxLayout()

        # Create setting group box
        settingGroup = QGroupBox("Settings")
        settingGroup.setMaximumWidth(250)
        settingGroup.setMaximumWidth(225)
        settingVBoxLayout = QVBoxLayout()
        symbolName = self.symbol.name if isinstance(self.symbol, Symbol) else self.symbol
        symblLbl = QLabel("Symbol: " + symbolName)
        symblLbl.setStyleSheet("font-weight: bold")
        symblLbl.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        symblLbl.setMaximumHeight(30)
        settingVBoxLayout.addWidget(symblLbl, alignment=Qt.AlignTop)
        # Draw Bar types
        self.barTypesCombo = QComboBox()
        for barType in BAR_TYPES:
            self.barTypesCombo.addItem(barType)
        settingVBoxLayout.addWidget(self.barTypesCombo, alignment=Qt.AlignTop)

        sboxLayout, self.widgetDict = createSettingsBox(self.defaultSettings)
        settingVBoxLayout.addLayout(sboxLayout)
        spacer = QSpacerItem(200, 200, QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        settingVBoxLayout.addSpacerItem(spacer)
        settingGroup.setLayout(settingVBoxLayout)

        self.chartWidget = CandleSticksWidget(
            parent=self,
            symbol=self.symbol,
            barFeed=self.barFeed,
            startDate=self.startDate,
            endDate=self.endDate,
            initWidth=self.adjustedWidth-225)

        layout.addWidget(settingGroup)
        layout.addWidget(self.chartWidget)

        self.layout = layout
        self.setLayout(layout)
