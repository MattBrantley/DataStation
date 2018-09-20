from PyQt5.Qt import *
from pyqtgraph.console import ConsoleWidget
import os

class consoleDockWidget(QDockWidget):
    ITEM_GUID = Qt.UserRole

    def __init__(self, mW):
        super().__init__('Interactive Console')
        self.mW = mW 
        self.consoleWidget = ConsoleWidget(self.mW)
        self.setWidget(self.consoleWidget)