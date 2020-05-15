import os
import re
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from threading import Event
from qpython.qconnection import MessageType
from qpython.qcollection import QDictionary

from fxqu4nt.utils.common import get_tmp_dir
from fxqu4nt.market.symbol import Symbol
from fxqu4nt.logger import create_logger
from fxqu4nt.market.kdb import get_db


class ImportTickListener(QRunnable):
    def __init__(self, setTextFn, enableCloseFn, q=None, file=None):
        super(ImportTickListener, self).__init__()
        self.logger = create_logger(self.__class__.__name__)
        self._stopper = Event()
        self.q = q
        self.file = file
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
            self.setTextFn("Importing " + self.file + "...")
            if message.type != MessageType.ASYNC:
                continue

            if isinstance(message.data, bytes):
                if message.data == b'TASK_DONE':
                    last_date = prev_date
                    self.setTextFn("Imported quotes data from %s to %s" % (first_date, last_date))
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

# https://www.learnpyqt.com/courses/concurrent-execution/multithreading-pyqt-applications-qthreadpool/
# https://stackoverflow.com/questions/50930792/pyqt-multiple-qprocess-and-output
class SplitCsvByMonth(QRunnable):
    def __init__(self, file=None):
        super(SplitCsvByMonth, self).__init__()
        self.file = file

    @pyqtSlot()
    def run(self):
        pass


class DateProcessedDialog(QDialog):
    def __init__(self, parent=None, q=None, file=None):
        self.parent = parent
        QDialog.__init__(self)
        self.file = file
        self.threadpool = QThreadPool()
        self.createLayout()
        worker = ImportTickListener(self.setTextFn, self.enableClose, q, file)
        self.threadpool = QThreadPool()
        self.threadpool.start(worker)

    def setTextFn(self, text):
        self.infoLabel.setText(text)

    def enableClose(self):
        self.okBnt.setEnabled(True)

    def okBntCicked(self):
        self.close()

    def createLayout(self):
        # self.setFixedWidth(300)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        layout = QVBoxLayout()
        self.infoLabel = QLabel("Importing " + self.file + "...")
        layout.addWidget(self.infoLabel)
        self.okBnt = QPushButton("Ok")
        self.okBnt.setEnabled(False)
        self.okBnt.clicked.connect(self.okBntCicked)
        layout.addWidget(self.okBnt)
        self.layout = layout
        self.setLayout(self.layout)


class SymbolSettingDialog(QDialog):
    """ Dialog controls symbols's settings"""
    def __init__(self, addSymbolCallback=None):
        QDialog.__init__(self)
        self.logger = create_logger(self.__class__.__name__, "info")
        self.setModal(True)
        self.setWindowTitle("Add Symbol")
        self.createLayout()
        self.kdb = get_db()
        self.addSymbolCallback = addSymbolCallback

    def createLayout(self):
        self.layout = QVBoxLayout(self)

        self.formGroupBox = QGroupBox("Symbol Settings")
        formLayout = QFormLayout()
        self.nameBox = QLineEdit()
        formLayout.addRow(QLabel("Name:"), self.nameBox)

        fileDialogLayout = QHBoxLayout()
        fileDialogLayout.setAlignment(Qt.AlignLeft)
        self.tickDataBox = QLineEdit()
        fileDialogLayout.addWidget(self.tickDataBox)
        bntFileDialog = QPushButton("...")
        bntFileDialog.setStyleSheet("padding: 5px")
        fileDialogLayout.addWidget(bntFileDialog)
        bntFileDialog.clicked.connect(self.bntFileDialogOnClicked)
        formLayout.addRow(QLabel("Tick Data:"), fileDialogLayout)

        self.pointBox = QLineEdit("0.00001")
        formLayout.addRow(QLabel("Point:"), self.pointBox)
        self.minVolBox = QLineEdit("0.01")
        formLayout.addRow(QLabel("Minimal Volume:"), QLineEdit("0.01"))
        self.maxVolBox = QLineEdit("10000")
        formLayout.addRow(QLabel("Maximal Volume:"), QLineEdit("10000"))
        self.volStepBox = QLineEdit("0.01")
        formLayout.addRow(QLabel("Volume Step:"), QLineEdit("0.01"))
        self.saveCheckBox = QCheckBox()
        self.saveCheckBox.setChecked(True)
        formLayout.addRow(QLabel("Save to disk:"), self.saveCheckBox)
        self.formGroupBox.setLayout(formLayout)
        self.layout.addWidget(self.formGroupBox)

        bntGroupBox = QHBoxLayout()
        bntGroupBox.setAlignment(Qt.AlignCenter)
        self.bntOk = QPushButton("Ok")
        self.bntOk.clicked.connect(self.bntOkOnClicked)
        self.bntCancel = QPushButton("Cancel")
        self.bntCancel.clicked.connect(self.bntCancelOnClicked)
        bntGroupBox.addWidget(self.bntOk)
        bntGroupBox.addWidget(self.bntCancel)

        self.layout.addLayout(bntGroupBox)

        self.setLayout(self.layout)

    def bntOkOnClicked(self):
        """ Hanle when OK button clicked """
        msgBox = QMessageBox()
        bInvalid = False
        errorMsg = ""
        symbolName = self.nameBox.text().strip()
        symbolPoint = self.pointBox.text().strip()
        symbolMinVol = self.minVolBox.text().strip()
        symbolMaxVol = self.maxVolBox.text().strip()
        symbolVolStep = self.volStepBox.text().strip()
        symbolTickData = self.tickDataBox.text().strip()

        if re.match("^[A-Z]+$", symbolName) is None:
            bInvalid = True
            errorMsg = "Symbol Name invalid"
        elif re.match("^0\.0{1,5}1$", symbolPoint) is None:
            bInvalid = True
            errorMsg = "Symbol Point invalid"
        elif re.match("^[0-9]{1,5}(\.[0-9]{1,5})?$", symbolMinVol) is None:
            bInvalid = True
            errorMsg = "Symbol Minimal Volume invalid"
        elif re.match("^[0-9]{1,5}(\.[0-9]{1,5})?$", symbolMaxVol) is None:
            bInvalid = True
            errorMsg = "Symbol Maximal Volume invalid"
        elif re.match("^[0-9]{1,5}(\.[0-9]{1,5})?$", symbolVolStep) is None:
            bInvalid = True
            errorMsg = "Symbol Volume Step invalid"
        elif not os.path.exists(symbolTickData):
            bInvalid = True
            errorMsg = "Path to symbol tick data doesn't exist"

        if bInvalid:
            msgBox.setWindowTitle("Add Symbol Error")
            msgBox.setIcon(QMessageBox.Critical)
            msgBox.setText(errorMsg)
            msgBox.exec_()
            return
        else:
            symbolPoint = float(symbolPoint)
            symbolMinVol = float(symbolMinVol)
            symbolMaxVol = float(symbolMaxVol)
            symbolVolStep = float(symbolVolStep)

            if symbolPoint > symbolVolStep:
                bInvalid = True
                errorMsg = "Symbol Point cannot be greater than Symbol Volume Step"
            elif symbolVolStep > symbolMinVol:
                bInvalid = True
                errorMsg = "Symbol Volume Step cannot be greater than Symbol Minimal Volume"
            elif symbolMinVol > symbolMaxVol:
                bInvalid = True
                errorMsg = "Symbol Minimal Volume cannot be greater than Symbol Maximal Volume"

            if bInvalid:
                msgBox.setWindowTitle("Add Symbol Error")
                msgBox.setIcon(QMessageBox.Critical)
                msgBox.setText(errorMsg)
                msgBox.exec_()
                return
            # check exist symbols
            if self.kdb.is_symbol_exist(symbolName):
                msgBox.setWindowTitle("Add Symbol Error")
                msgBox.setIcon(QMessageBox.Critical)
                msgBox.setText("Symbol %s was existed, please use update to change symbol's settings" % symbolName)
                msgBox.exec_()
                return

            symbol = Symbol(name=symbolName,
                            point=symbolPoint,
                            min_vol=symbolMinVol,
                            max_vol=symbolMaxVol,
                            vol_step=symbolVolStep)
            if self.kdb.add_symbol(symbol):
                if self.saveCheckBox.isChecked():
                    pdialog = DateProcessedDialog(self, q=self.kdb.q, file=symbolTickData)
                    self.kdb.async_add_tick_data(symbol, symbolTickData)
                    self.hide()
                    pdialog.exec_()
                else:
                    self.kdb.add_tick_data(symbol, symbolTickData)
                self.addSymbolCallback(symbol)
        self.close()

    def bntCancelOnClicked(self):
        self.close()

    def bntFileDialogOnClicked(self):
        fileDlg = QFileDialog()
        fileDlg.setNameFilter("CSV (*.csv)")
        fileDlg.setOption(QFileDialog.DontUseNativeDialog, True)
        fileDlg.setOption(QFileDialog.ShowDirsOnly, False)

        if fileDlg.exec_():
            filenames = fileDlg.selectedFiles()
            if len(filenames):
                self.tickDataBox.setText(filenames[0])
