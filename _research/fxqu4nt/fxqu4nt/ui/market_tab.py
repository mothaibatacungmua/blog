import os
import re
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from fxqu4nt.market.kdb import get_db
from fxqu4nt.logger import create_logger


class SymbolSettingDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.logger = create_logger(self.__class__.__name__, "info")
        self.setModal(True)
        self.setWindowTitle("Add Symbol")
        self.createLayout()
        self.kdb = get_db()

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
            symbolMeta = self.kdb.get_symbols()
            if symbolName in symbolMeta.index:
                msgBox.setWindowTitle("Add Symbol Error")
                msgBox.setIcon(QMessageBox.Critical)
                msgBox.setText("Symbol %s was existed, please use update to change symbol's settings" % symbolName)
                msgBox.exec_()
                return

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


class MarketTabWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.createLayout()

    def createLayout(self):
        self.layout = QHBoxLayout()

        lvbox = QVBoxLayout()
        symbolListWidget = QListWidget()
        lvbox.addWidget(symbolListWidget)

        bntvbox = QVBoxLayout()
        bntvbox.setAlignment(Qt.AlignTop)

        addBnt = QPushButton("Add")
        addBnt.clicked.connect(self.openAddSymbolDialog)
        bntvbox.addWidget(addBnt)

        removeBnt = QPushButton("Remove")
        bntvbox.addWidget(removeBnt)

        kdbRestoreBnt = QPushButton("Kdb+ Restore")
        bntvbox.addWidget(kdbRestoreBnt)

        self.layout.addLayout(lvbox)
        self.layout.addLayout(bntvbox)
        self.setLayout(self.layout)

    def openAddSymbolDialog(self):
        symbolDialog = SymbolSettingDialog()
        symbolDialog.exec_()
