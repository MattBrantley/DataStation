from PyQt5.Qt import *

class progressBarDockWidget(QDockWidget):
    ITEM_GUID = Qt.UserRole

    def __init__(self, mW):
        super().__init__('Progress Bar')
        self.mW = mW
        self.progressBar = QProgressBar()
        self.setWidget(self.progressBar)
        