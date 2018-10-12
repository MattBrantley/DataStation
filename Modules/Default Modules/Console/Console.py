from PyQt5.Qt import *
from pyqtgraph.console import ConsoleWidget
import os
from src.Managers.ModuleManager.DSModule import DSModule
from src.Constants import moduleFlags as mfs

class Console(DSModule):
    Module_Name = 'Console'
    Module_Flags = []
    ITEM_GUID = Qt.UserRole

    def __init__(self, ds, handler):
        super().__init__(ds, handler)
        self.ds = ds 

    def configureWidget(self, window):
        self.window = window
        self.consoleWidget = ConsoleWidget(self.window)
        self.setWidget(self.consoleWidget)