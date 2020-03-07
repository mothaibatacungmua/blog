from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from fxqu4nt.ui.database_tab import DatabaseTabWidget
from fxqu4nt.ui.market_tab import MarketTabWidget


class MainWidget(QWidget):
    def __init__(self, mwd=None):
        QWidget.__init__(self)
        self.mwd = mwd
        self.createLayout()

    def createLayout(self):
        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.marketTab = MarketTabWidget()
        self.databaseTab = DatabaseTabWidget()

        self.tabs.addTab(self.marketTab, "Market")
        self.tabs.addTab(self.databaseTab, "Database")
        self.tabs.currentChanged.connect(self.onTabChanged)
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

    def onTabChanged(self, idx):
        if idx == 1:
            self.databaseTab.refresh()