import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from fxqu4nt.logger import create_logger


class SymbolSettingDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.logger = create_logger(self.__class__.__name__, "info")
        self.setModal(True)
        self.setWindowTitle("Add Symbol")
        self.createLayout()

    def createLayout(self):
        self.layout = QVBoxLayout(self)

        self.formGroupBox = QGroupBox("Symbol Settings")
        formLayout = QFormLayout()
        formLayout.addRow(QLabel("Name:"), QLineEdit())

        fileDialogLayout = QHBoxLayout()
        fileDialogLayout.setAlignment(Qt.AlignLeft)
        fileDialogLayout.addWidget(QLineEdit())
        bntFileDialog = QPushButton("...")
        bntFileDialog.setStyleSheet("padding: 5px")
        fileDialogLayout.addWidget(bntFileDialog)
        formLayout.addRow(QLabel("Tick Data:"), fileDialogLayout)
        formLayout.addRow(QLabel("Point:"), QLineEdit())
        formLayout.addRow(QLabel("Minimum Lots:"), QLineEdit("0.01"))
        formLayout.addRow(QLabel("Maximum Lots:"), QLineEdit("10000"))

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
        pass

    def bntCancelOnClicked(self):
        self.close()


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
