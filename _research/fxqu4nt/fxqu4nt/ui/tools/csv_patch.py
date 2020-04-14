import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from fxqu4nt.utils.csv_tick_file import CsvTickFile
from fxqu4nt.logger import create_logger


class PatchRunner(QThread):
    def __init__(self, widget):
        super(PatchRunner, self).__init__()
        self.widget = widget
        self.logger = create_logger(self.__class__.__name__)

    @pyqtSlot()
    def run(self):
        widget = self.widget
        widget.canClose = False
        csvTickFile = CsvTickFile(widget.filePathEdit.text())
        widget.processBnt.setText("0%")

        def cbfn(fobj):
            fsize = csvTickFile.fsize
            processed = fobj.tell()
            percent = int(processed / fsize * 100)
            widget.processBnt.setText("%d%%" % percent)

        try:
            csvTickFile.fix_date(cbfn)
        except Exception as e:
            self.logger.error(e)
            widget.sigProcessError.emit(str(e))
        widget.processBnt.setDisabled(False)
        widget.processBnt.setText("Process")
        widget.canClose = True


class CsvPatchDialog(QDialog):
    sigProcessError = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setModal(True)
        self.createLayout()
        self.canClose = True
        self.patching = False
        self.sigProcessError.connect(self.showErrorBox)

    def showMsgBox(self,title, message, icon):
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle(title)
        msgBox.setIcon(icon)
        msgBox.setText(message)
        msgBox.exec_()

    def showErrorBox(self, message):
        self.showMsgBox("Patch Error!", message, QMessageBox.Critical)

    def createLayout(self):
        self.setWindowTitle("Patch Quotes CSV")
        self.layout = QVBoxLayout()

        formLayout = QFormLayout()

        fileDialogLayout = QHBoxLayout()
        fileDialogLayout.setAlignment(Qt.AlignLeft)
        self.filePathEdit = QLineEdit()
        fileDialogLayout.addWidget(self.filePathEdit)
        bntFileDialog = QPushButton("...")
        bntFileDialog.setStyleSheet("padding: 5px")
        bntFileDialog.clicked.connect(self.bntFileDialogOnClick)

        fileDialogLayout.addWidget(bntFileDialog)
        formLayout.addRow(QLabel("Storage:"), fileDialogLayout)
        self.layout.addLayout(formLayout)

        self.processBnt = QPushButton("Process")
        self.processBnt.clicked.connect(self.bntProcessOnClick)
        self.layout.addWidget(self.processBnt)

        self.setLayout(self.layout)

    def bntFileDialogOnClick(self):
        fileDlg = QFileDialog()
        fileDlg.setFileMode(QFileDialog.AnyFile)
        fileDlg.setNameFilters(['CSV (*.csv)'])

        if fileDlg.exec_():
            filenames = fileDlg.selectedFiles()
            if len(filenames):
                self.filePathEdit.setText(filenames[0])

    def bntProcessOnClick(self):
        if not os.path.exists(self.filePathEdit.text()):
            self.showMsgBox("Patch Error!", "File doesn't exist", QMessageBox.Critical)

        self.worker = PatchRunner(self)
        self.worker.finished.connect(self.taskDone)
        self.worker.start()

        self.processBnt.setDisabled(True)

    def taskDone(self):
        self.showMsgBox("Done!", "Patch successfully", QMessageBox.Information)

    def closeEvent(self, event):
        if self.canClose:
            event.accept()
            return
        event.ignore()