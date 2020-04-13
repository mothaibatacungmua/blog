from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from fxqu4nt.ui.database_tab import DatabaseTabWidget
from fxqu4nt.ui.market_tab import MarketTabWidget
from fxqu4nt.ui.tools_tab import ToolsTabWidget


class MainWidget(QWidget):
    def __init__(self, mwd=None):
        QWidget.__init__(self)
        self.mwd = mwd
        self.createLayout()

    def createLayout(self):
        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.marketTab = MarketTabWidget()
        self.toolTab = ToolsTabWidget()
        self.databaseTab = DatabaseTabWidget()

        self.tabs.addTab(self.marketTab, "Market")
        self.tabs.addTab(self.toolTab, "Tools")
        self.tabs.addTab(self.databaseTab, "Database")
        self.tabs.currentChanged.connect(self.onTabChanged)
        self.layout.addWidget(self.tabs)

        self.setLayout(self.layout)

    def onTabChanged(self, idx):
        if idx == 1:
            self.databaseTab.refresh()