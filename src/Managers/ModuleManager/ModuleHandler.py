from PyQt5.Qt import *
import sys
from os.path import dirname

class ModuleHandler(QObject):
############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################

    def Assign_To_Window(self, window):
        self.assignToWindow(window)

############################################################################################
#################################### INTERNAL USER ONLY ####################################
    def __init__(self, modObject, window, mW):
        super().__init__()
        self.mW = mW
        self.mM = mW.mM
        self.modObject = modObject
        self.window = window

        self.instantiateModule()
        self.Assign_To_Window(window)

    def instantiateModule(self):
        #oldPath = sys.path
        #sys.path.append(dirname(self.modOBject.filePath))
        self.modInstance = self.modObject.modClass(self.mW)
        self.modInstance.setWindowTitle(self.modObject.name)

        #sys.path = oldPath

    def assignToWindow(self, window):
        self.window.transferModule(self.modInstance)