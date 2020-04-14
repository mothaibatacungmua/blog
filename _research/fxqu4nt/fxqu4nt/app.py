import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import QtGui

from fxqu4nt.ui.widget import MarketWidget, DatabaseDialog
from fxqu4nt.ui.tools import CsvPatchDialog
from fxqu4nt.settings import PACKAGE_NAME, VERSION, get_all_q_script_paths, get_all_q_utils_paths
from fxqu4nt.market.kdb import get_db
from fxqu4nt.logger import create_logger

# https://github.com/constverum/Quantdom/blob/master/quantdom/app.py

class MainWindow(QMainWindow):
    size = (480, 320)

    def __init__(self, parent=None):
        self.logger = create_logger(self.__class__.__name__, "info")
        self.kdb = get_db()
        self.kdb.restore_all()
        super().__init__(parent)

        scriptDir = os.path.dirname(os.path.realpath(__file__))
        iconPath = os.path.join(scriptDir, "resources/icon.ico")
        icon = QtGui.QIcon(iconPath)
        self.centralWidget = QStackedWidget()
        self.marketWidget = MarketWidget(self)
        self.databaseDialog = DatabaseDialog(self)

        self.centralWidget.addWidget(self.marketWidget)
        self.centralWidget.setCurrentWidget(self.marketWidget)
        self.setCentralWidget(self.centralWidget)
        self.setMinimumSize(*self.size)
        self.setWindowIcon(icon)
        self.setWindowTitle(PACKAGE_NAME + " " + VERSION)
        self.resize(*self.size)
        self._moveToCenter()
        self._loadQScripts()

        self.initUi()

    def initUi(self):
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        toolsMenu = menuBar.addMenu('&Tools')

        market = QAction('&Market', self)
        market.triggered.connect(self.onMarket)
        fileMenu.addAction(market)
        database = QAction('&Database', self)
        database.triggered.connect(self.onDatabase)
        fileMenu.addAction(database)
        exit_ = QAction('E&xit', self)
        exit_.triggered.connect(self.close)
        fileMenu.addAction(exit_)

        csvPatch = QAction('&Patch CSV', self)
        csvPatch.triggered.connect(self.onCsvPatch)
        toolsMenu.addAction(csvPatch)

    def onCsvPatch(self):
        CsvPatchDialog(self).exec_()

    def onMarket(self):
        self.centralWidget.setCurrentWidget(self.marketWidget)

    def onDatabase(self):
        self.databaseDialog.refresh()
        self.databaseDialog.exec_()

    def _loadQScripts(self):
        for sp in get_all_q_utils_paths():
            self.kdb.load_script(sp)
        for sp in get_all_q_script_paths():
            self.kdb.load_script(sp)

    def _moveToCenter(self):
        desktop = QApplication.desktop()
        x = (desktop.width() - self.width())/2
        y = (desktop.height() - self.height())/2
        self.move(int(x), int(y))

    def closeEvent(self, event):
        self.logger.info("Close Kdb+ connection...")
        self.kdb.close()


def main():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    app.setApplicationName(PACKAGE_NAME)
    app.setApplicationVersion(VERSION)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()