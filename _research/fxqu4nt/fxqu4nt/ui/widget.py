from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class SymbolSettingDialog(QDialog):
    def __init__(self):
        super().__init__()
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
        self.setLayout(self.layout)


class MainWidget(QWidget):
    def __init__(self, mwd=None):
        super().__init__()
        self.mwd = mwd
        self.createLayout()

    def createLayout(self):
        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.marketTab = self.marketTabUI()
        self.databaseTab = self.databaseTabUI()

        self.tabs.addTab(self.marketTab, "Market")
        self.tabs.addTab(self.databaseTab, "Database")

        self.layout.addWidget(self.tabs)

        self.setLayout(self.layout)

    def marketTabUI(self):
        tab = QWidget()
        tab.layout = QHBoxLayout()

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

        tab.layout.addLayout(lvbox)
        tab.layout.addLayout(bntvbox)
        tab.setLayout(tab.layout)

        return tab

    def databaseTabUI(self):
        tab = QWidget()
        tab.layout = QVBoxLayout()

        settingLayout = QFormLayout()
        settingLayout.addRow(QLabel("Host"), QLineEdit("localhost"))
        settingLayout.addRow(QLabel("Port"), QLineEdit("5042"))

        bntLayout = QHBoxLayout()
        saveBnt = QPushButton("Save")
        bntLayout.addWidget(saveBnt)
        testConnectBnt = QPushButton("Test Connection")
        bntLayout.addWidget(testConnectBnt)
        defaultBnt = QPushButton("Default")
        bntLayout.addWidget(defaultBnt)

        tab.layout.addLayout(settingLayout)
        tab.layout.addLayout(bntLayout)

        tab.setLayout(tab.layout)
        return tab

    def openAddSymbolDialog(self):
        symbolDialog = SymbolSettingDialog()
        symbolDialog.exec_()