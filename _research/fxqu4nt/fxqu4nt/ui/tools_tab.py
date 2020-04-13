from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class ToolsTabWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

