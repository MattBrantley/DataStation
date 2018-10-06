from PyQt5.Qt import *
from pyqtgraph.console import ConsoleWidget
import os
from src.Managers.ModuleManager.DSModule import DSModule
from src.Constants import moduleFlags as mfs

class Console(DSModule):
    Module_Name = 'Console'
    Module_Flags = [mfs.SHOW_ON_CREATION, mfs.FLOAT_ON_CREATION]
    ITEM_GUID = Qt.UserRole

    def __init__(self, mW):
        super().__init__(mW)
        self.mW = mW 
        self.consoleWidget = ConsoleWidget(self.mW)
        self.setWidget(self.consoleWidget)