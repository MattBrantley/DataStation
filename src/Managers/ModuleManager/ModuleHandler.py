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
    def __init__(self, modObject, window, ds, uuid):
        super().__init__()
        self.ds = ds
        self.mM = ds.mM
        self.modObject = modObject
        self.window = window
        self.uuid = uuid

        self.instantiateModule()
        self.Assign_To_Window(window)

    def instantiateModule(self):
        self.modInstance = self.modObject.modClass(self.ds)
        self.modInstance.setObjectName(self.uuid)
        self.modInstance.setWindowTitle(self.modObject.name)

    def assignToWindow(self, window):
        self.window.transferModule(self)
        self.modInstance.configureWidget(self.window)
