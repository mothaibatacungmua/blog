import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from fxqu4nt.settings import save_mcnf, get_mcnf
from fxqu4nt.market.kdb import get_db


class DatabaseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.setModal(True)
        self.cnf = get_mcnf()
        if self.cnf is None:
            self.cnf = {}
        self.createLayout()

    def createLayout(self):
        self.setWindowTitle("Kdb+/Q Server Settings")
        self.layout = QVBoxLayout()

        settingLayout = QFormLayout()
        self.hostLineEdit = QLineEdit(self.cnf.get("host", "localhost"))
        self.hostLineEdit.textChanged.connect(self.onTextChanged)
        self.portLineEdit = QLineEdit(self.cnf.get("port","5042"))
        self.portLineEdit.textChanged.connect(self.onTextChanged)
        settingLayout.addRow(QLabel("Host"), self.hostLineEdit)
        settingLayout.addRow(QLabel("Port"), self.portLineEdit)

        fileDialogLayout = QHBoxLayout()
        fileDialogLayout.setAlignment(Qt.AlignLeft)
        self.storageLineEdit = QLineEdit(self.cnf.get("storage",""))
        self.storageLineEdit.textChanged.connect(self.onTextChanged)
        fileDialogLayout.addWidget(self.storageLineEdit)
        bntFileDialog = QPushButton("...")
        bntFileDialog.setStyleSheet("padding: 5px")
        bntFileDialog.clicked.connect(self.bntFileDialogOnClick)

        fileDialogLayout.addWidget(bntFileDialog)
        settingLayout.addRow(QLabel("Storage:"), fileDialogLayout)

        bntLayout = QHBoxLayout()
        self.bntSave = QPushButton("Save")
        self.bntSave.setEnabled(False)
        self.bntSave.clicked.connect(self.bntSaveOnClick)
        bntLayout.addWidget(self.bntSave)

        testConnectBnt = QPushButton("Test Connection")
        testConnectBnt.clicked.connect(self.testConnectBntOnClick)
        bntLayout.addWidget(testConnectBnt)

        self.defaultBnt = QPushButton("Default")
        self.defaultBnt.clicked.connect(self.defaultBntOnClick)
        bntLayout.addWidget(self.defaultBnt)

        self.layout.addLayout(settingLayout)
        self.layout.addLayout(bntLayout)

        self.setLayout(self.layout)

    def testConnectBntOnClick(self):
        host = self.hostLineEdit.text()
        port = int(self.portLineEdit.text())

        quotes_db = get_db(host, port)

        msgBox = QMessageBox()
        if quotes_db.test():
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText("Successfully connect to Kdb+ server!")
        else:
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setText("Failed to connect to Kdb+ server!")

        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec_()

    def bntFileDialogOnClick(self):
        fileDlg = QFileDialog()
        fileDlg.setFileMode(QFileDialog.DirectoryOnly)
        fileDlg.setOption(QFileDialog.DontUseNativeDialog, True)
        fileDlg.setOption(QFileDialog.ShowDirsOnly, True)

        if fileDlg.exec_():
            filenames = fileDlg.selectedFiles()
            if len(filenames):
                self.storageLineEdit.setText(filenames[0])

    def bntSaveOnClick(self):
        storagePath = self.storageLineEdit.text()
        if os.path.exists(storagePath):
            cnf = {
                'host': self.hostLineEdit.text(),
                'port': self.portLineEdit.text(),
                'storage': storagePath
            }
            save_mcnf(cnf)
            self.cnf = cnf
        else:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setText("Storage path is not exist!")
            msgBox.exec_()

        self.bntSave.setEnabled(False)

    def onTextChanged(self):
        self.bntSave.setEnabled(True)

    def defaultBntOnClick(self):
        self.cnf = {
            "host": "localhost",
            "port": "5042",
            "storage": ""
        }
        self.hostLineEdit.setText(self.cnf["host"])
        self.portLineEdit.setText(self.cnf["port"])
        self.storageLineEdit.setText(self.cnf["storage"])

    def refresh(self):
        self.cnf = get_mcnf()
        self.hostLineEdit.setText(self.cnf["host"])
        self.portLineEdit.setText(self.cnf["port"])
        self.storageLineEdit.setText(self.cnf["storage"])

        self.bntSave.setEnabled(False)