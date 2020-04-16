from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


from fxqu4nt.market.kdb import get_db
from fxqu4nt.market.symbol import Symbol
from fxqu4nt.ui.symbol_view import ViewSymbol
from fxqu4nt.ui.symbol_import import SymbolSettingDialog
from fxqu4nt.ui.bar_gen import BarGenDialog

class SymbolListWidget(QListWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self)
        self.parent = parent
        self.kdb = get_db()
        self.createLayout()

    def createLayout(self):
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.itemClicked.connect(self.onItemClick)
        self.viewport().installEventFilter(self)

        symbolMeta = self.kdb.get_symbols()
        if symbolMeta is not None:
            for symbol, row in symbolMeta.iterrows():
                self.addItem(symbol)

    def onItemClick(self, item: QListWidgetItem):
        pass

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.MouseButtonPress and source is self.viewport():
            if event.button() == Qt.RightButton:
                item = self.itemAt(event.pos())
                if item:
                    self.setCurrentItem(item)
                    menu = QMenu()
                    viewAction = QAction('View', self)
                    viewAction.triggered.connect(self.viewSymbolCall)
                    updateAction = QAction('Update', self)
                    updateAction.triggered.connect(self.updateSymbolCall)
                    menu.addAction(viewAction)
                    menu.addAction(updateAction)
                    if menu.exec_(event.globalPos()):
                        return True
        return super(QListWidget, self).eventFilter(source, event)

    def viewSymbolCall(self):
        currentSymbol = self.currentItem().text()
        currentSymbol = self.kdb.get_symbol(currentSymbol)
        viewDialog = ViewSymbol(symbol=currentSymbol, parent=self)
        viewDialog.show()

    def updateSymbolCall(self):
        pass


class MarketWidget(QWidget):
    """ Widget display list imported symbols """
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.parent = parent
        self.kdb = get_db()
        self.createLayout()

    def createLayout(self):
        self.layout = QHBoxLayout()

        lvbox = QVBoxLayout()
        self.symbolListWidget = SymbolListWidget()

        lvbox.addWidget(self.symbolListWidget)
        bntvbox = QVBoxLayout()
        bntvbox.setAlignment(Qt.AlignTop)

        addBnt = QPushButton("Add")
        addBnt.clicked.connect(self.openAddSymbolDialog)
        bntvbox.addWidget(addBnt)

        removeBnt = QPushButton("Remove")
        bntvbox.addWidget(removeBnt)
        removeBnt.clicked.connect(self.onRemoveBntClicked)

        barsGeneratorBnt = QPushButton("Bars Generator")
        bntvbox.addWidget(barsGeneratorBnt)
        barsGeneratorBnt.clicked.connect(self.onBarsGeneratorBntClicked)

        self.layout.addLayout(lvbox)
        self.layout.addLayout(bntvbox)
        self.setLayout(self.layout)

    def openAddSymbolDialog(self):
        symbolDialog = SymbolSettingDialog(
                        addSymbolCallback=self.addSymbolToList)
        symbolDialog.exec_()

    def addSymbolToList(self, symbol: Symbol):
        self.symbolListWidget.addItem(symbol.name)

    def onRemoveBntClicked(self):
        item = self.symbolListWidget.currentItem()
        if item is None:
            return
        symbol = item.text()

        if self.kdb.remove_symbol(symbol):
            self.kdb.remove_symbol_quotes(symbol)

        self.symbolListWidget.takeItem(self.symbolListWidget.row(item))

    def onBarsGeneratorBntClicked(self):
        item = self.symbolListWidget.currentItem()
        if item is None:
            return
        symbol = item.text()
        symbol = self.kdb.get_symbol(symbol)

        barGenDlg = BarGenDialog(self, symbol=symbol)
        barGenDlg.exec_()