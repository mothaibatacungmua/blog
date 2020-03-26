import sys

from PyQt5.QtWidgets import QMainWindow, QApplication

from fxqu4nt.ui.widget import MainWidget
from fxqu4nt.settings import PACKAGE_NAME, VERSION, get_all_q_script_paths
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
        self.main_widget = MainWidget(self)
        self.setCentralWidget(self.main_widget)
        self.setMinimumSize(*self.size)
        self.setWindowTitle(PACKAGE_NAME + " " + VERSION)
        self.resize(*self.size)
        self._move_to_center()
        self._load_q_scripts()

    def _load_q_scripts(self):
        for sp in get_all_q_script_paths():
            self.kdb.load_script(sp)

    def _move_to_center(self):
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