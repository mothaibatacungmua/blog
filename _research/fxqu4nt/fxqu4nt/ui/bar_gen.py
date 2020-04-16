import os
import re
import time
from threading import Event
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from fxqu4nt.market.symbol import Symbol

TICK_BAR = "Tick Bar"
TICK_VOLUME_BAR = "Tick Volume Bar"
TIME_BAR = "Time Bar"
BAR_TYPES = [TICK_BAR, TICK_VOLUME_BAR, TIME_BAR]
TIMEFRAMES = ["M1", "M2", "M3", "M4", "M5", "M6", "M10", "M12", "M15", "M20", "M30", "H1", "H2", "H3", "H4", "H6", "H8", "H12", "Daily", "Weekly"]


class TickBarSettings(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.createLayout()

    def createLayout(self):
        formBox = QFormLayout()
        self.barSizeEdit = QLineEdit("50")
        formBox.addRow(QLabel("Bar size:"), self.barSizeEdit)
        self.layout = formBox
        self.setLayout(self.layout)

class TickVolumeBarSettings(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.createLayout()

    def createLayout(self):
        formBox = QFormLayout()
        self.volumeSizeEdit = QLineEdit("50")
        formBox.addRow(QLabel("Volume size:"), self.volumeSizeEdit)
        self.layout = formBox
        self.setLayout(self.layout)


class TimeBarSettings(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.createLayout()

    def createLayout(self):
        formBox = QFormLayout()
        self.timeframes = QComboBox()
        for tf in TIMEFRAMES:
            self.timeframes.addItem(tf)
        self.timeframes.currentIndexChanged.connect(self.onIndexChanged)
        formBox.addRow(QLabel("Timeframes:"), self.timeframes)
        self.layout = formBox
        self.setLayout(self.layout)

    def onIndexChanged(self, i):
        print(self.timeframes.currentText())


class BarGenDialog(QDialog):
    def __init__(self, parent=None, symbol:Symbol=None):
        super().__init__(parent)
        self.parent = parent
        self.symbol = symbol
        self.setModal(True)

        self.createLayout()

    def createLayout(self):
        self.setWindowTitle(self.symbol.name +" Bar Generator")
        self.barTypesCombo = QComboBox()

        settingGroup = QGroupBox("Settings")
        settingVBoxLayout = QVBoxLayout()
        self.barTypesCombo = QComboBox()
        for barType in BAR_TYPES:
            self.barTypesCombo.addItem(barType)
        self.barTypesCombo.currentIndexChanged.connect(self.onBarTypeChanged)
        settingVBoxLayout.addWidget(self.barTypesCombo, alignment=Qt.AlignTop)

        self.stackedWidget = QStackedWidget()
        self.tickbarSettings = TickBarSettings(self)
        self.tickVolBarSettings = TickVolumeBarSettings(self)
        self.timeBarSettings = TimeBarSettings(self)
        self.stackedWidget.addWidget(self.tickbarSettings)
        self.stackedWidget.addWidget(self.tickVolBarSettings)
        self.stackedWidget.addWidget(self.timeBarSettings)
        self.stackedWidget.setCurrentWidget(self.tickbarSettings)
        settingVBoxLayout.addWidget(self.stackedWidget)

        settingGroup.setLayout(settingVBoxLayout)

        gridLayout = QGridLayout()
        gridLayout.addWidget(settingGroup, 0, 0, 1, 4)
        leftSpacer = QSpacerItem(50, 50, QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        rightSpacer = QSpacerItem(50, 50, QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        gridLayout.addItem(leftSpacer, 1, 0)
        genBnt = QPushButton("Generate")
        cancelBnt = QPushButton("Cancel")
        cancelBnt.clicked.connect(self.onCancelBntClick)
        gridLayout.addWidget(genBnt, 1, 1)
        gridLayout.addWidget(cancelBnt, 1, 2)
        gridLayout.addItem(rightSpacer, 1, 3)

        self.layout = gridLayout
        self.setLayout(self.layout)

    def onCancelBntClick(self):
        self.close()

    def onBarTypeChanged(self, i):
        if self.barTypesCombo.currentText() == TICK_BAR:
            self.stackedWidget.setCurrentWidget(self.tickbarSettings)
        elif self.barTypesCombo.currentText() == TICK_VOLUME_BAR:
            self.stackedWidget.setCurrentWidget(self.tickVolBarSettings)
        elif self.barTypesCombo.currentText() == TIME_BAR:
            self.stackedWidget.setCurrentWidget(self.timeBarSettings)