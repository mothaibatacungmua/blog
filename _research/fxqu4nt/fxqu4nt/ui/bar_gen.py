import os
import re
import time
from argparse import Namespace
from threading import Event
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from qpython.qconnection import MessageType
from qpython.qcollection import QDictionary

from fxqu4nt.market.kdb import get_db
from fxqu4nt.market.bar import TickBar
from fxqu4nt.market.symbol import Symbol
from fxqu4nt.logger import create_logger

TICK_BAR = "Tick Bar"
TICK_VOLUME_BAR = "Tick Volume Bar"
TIME_BAR = "Time Bar"
BAR_TYPES = [TICK_BAR, TICK_VOLUME_BAR, TIME_BAR]
TIMEFRAMES = ["M1", "M2", "M3", "M4", "M5", "M6", "M10", "M12", "M15", "M20", "M30", "H1", "H2", "H3", "H4", "H6", "H8", "H12", "Daily", "Weekly"]


class BarGenListerner(QRunnable):
    def __init__(self, setTextFn, enableCloseFn, q=None):
        super(BarGenListerner, self).__init__()
        self.logger = create_logger(self.__class__.__name__)
        self._stopper = Event()
        self.q = q
        self.setTextFn = setTextFn
        self.enableCloseFn = enableCloseFn

    def stop(self):
        self._stopper.set()

    def stopped(self):
        return self._stopper.isSet()

    @pyqtSlot()
    def run(self):
        prev_date = ""
        first_date = None

        while not self.stopped():
            message = self.q.receive(data_only=False, raw=False)
            self.setTextFn("Generating...")
            if message.type != MessageType.ASYNC:
                continue

            if isinstance(message.data, bytes):
                if message.data == b'TASK_DONE':
                    last_date = prev_date
                    self.setTextFn("Generated quotes data from %s to %s" % (first_date, last_date))
                    self.enableCloseFn()
                    self.stop()
                    continue
            if isinstance(message.data, QDictionary):
                next_date = message.data[b'processed'].decode("utf-8").strip()
                if len(next_date):
                    if next_date != prev_date:
                        prev_date = next_date
                        if first_date is None:
                            first_date = prev_date


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

    def getSettings(self):
        settings = dict()
        settings["barSize"] = int(self.barSizeEdit.text())

        return Namespace(**settings)


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

    def getSettings(self):
        settings = dict()
        settings["volSize"] = self.volumeSizeEdit.text()
        return Namespace(**settings)


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
        formBox.addRow(QLabel("Timeframes:"), self.timeframes)
        self.layout = formBox
        self.setLayout(self.layout)

    def getSettings(self):
        settings = dict()
        settings["timeframe"] = self.timeframes.currentText()
        return Namespace(**settings)


class BarGenDialog(QDialog):
    def __init__(self, parent=None, symbol:Symbol=None):
        super().__init__(parent)
        self.parent = parent
        self.symbol = symbol
        self.setModal(True)

        self.createLayout()

    def createLayout(self):
        self.setWindowFlags(
            Qt.Window |
            Qt.CustomizeWindowHint |
            Qt.WindowTitleHint |
            Qt.WindowStaysOnTopHint)
        # self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        # self.setWindowFlag(Qt.WindowCloseButtonHint, False)
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
        self.statusLbl = QLabel("Status:")
        gridLayout.addWidget(self.statusLbl, 1, 0, 1, 4)
        self.statusLbl.hide()
        leftSpacer = QSpacerItem(50, 50, QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        rightSpacer = QSpacerItem(50, 50, QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        gridLayout.addItem(leftSpacer, 2, 0)
        genBnt = QPushButton("Generate")
        genBnt.clicked.connect(self.onGenerateBntClick)
        self.cancelBnt = QPushButton("Cancel")
        self.cancelBnt.clicked.connect(self.onCancelBntClick)
        gridLayout.addWidget(genBnt, 2, 1)
        gridLayout.addWidget(self.cancelBnt, 2, 2)
        gridLayout.addItem(rightSpacer, 2, 3)

        self.layout = gridLayout
        self.setLayout(self.layout)

    def onGenerateBntClick(self):
        threadpool = QThreadPool()
        self.cancelBnt.setEnabled(False)
        self.statusLbl.setHidden(False)

        worker = BarGenListerner(self.setTextFn, self.enableCloseFn, get_db().q)
        threadpool.start(worker)

        settings = self.tickbarSettings.getSettings()
        tickBarGen = TickBar(
            kdb=get_db(),
            symbol=self.symbol,
            step_size=settings.barSize)
        tickBarGen.async_generate()

    def setTextFn(self, text):
        self.statusLbl.setText("Status: " + text)

    def enableCloseFn(self):
        self.cancelBnt.setEnabled(True)
        self.statusLbl.setText("Status:")
        self.statusLbl.hide()

    def onCancelBntClick(self):
        self.close()

    def onBarTypeChanged(self, i):
        if self.barTypesCombo.currentText() == TICK_BAR:
            self.stackedWidget.setCurrentWidget(self.tickbarSettings)
        elif self.barTypesCombo.currentText() == TICK_VOLUME_BAR:
            self.stackedWidget.setCurrentWidget(self.tickVolBarSettings)
        elif self.barTypesCombo.currentText() == TIME_BAR:
            self.stackedWidget.setCurrentWidget(self.timeBarSettings)