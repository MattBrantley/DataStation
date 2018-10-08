from PyQt5.Qt import *
import sys, uuid
from os.path import dirname

class ModuleHandler(QObject):
############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################

    def Assign_To_Window(self, window):
        self.assignToWindow(window)

############################################################################################
#################################### INTERNAL USER ONLY ####################################
    def __init__(self, modObject, window, mW, uuid):
        super().__init__()
        self.mW = mW
        self.mM = mW.mM
        self.modObject = modObject
        self.window = window
        self.uuid = uuid

        self.instantiateModule()
        self.Assign_To_Window(window)

    def instantiateModule(self):
        self.modInstance = self.modObject.modClass(self.mW)
        self.modInstance.setObjectName(self.uuid)
        self.modInstance.setWindowTitle(self.modObject.name)

    def assignToWindow(self, window):
        self.window.transferModule(self)
