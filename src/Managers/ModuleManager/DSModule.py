from PyQt5.Qt import *
import time, os
from src.Constants import moduleFlags as mfs

class DSModule(QDockWidget):
    Module_Name = 'Default'
    Module_Flags = []
    
############################################################################################
##################################### EXTERNAL SIGNALS #####################################
    

############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################

    def Get_Window(self):
        return self.window

    def Has_Flag(self, flag):
        if flag in self.Module_Flags:
            return True
        else:
            return False

############################################################################################
#################################### INTERNAL USER ONLY ####################################
    def __init__(self, ds):
        super().__init__()
        self.ds = ds
        self.modDataPath = os.path.join(ds.rootDir, 'Module Data/' + self.Module_Name)

        self.setFeatures(QDockWidget.DockWidgetMovable)

        if(self.Has_Flag(mfs.CAN_DELETE) or self.Has_Flag(mfs.CAN_HIDE)):
            self.setFeatures(self.features() | QDockWidget.DockWidgetClosable)
        if(self.Has_Flag(mfs.CAN_FLOAT)):
            self.setFeatures(self.features() | QDockWidget.DockWidgetFloatable)

    def configureWidget(self, window):
        pass #OVewrride this

    def closeEvent(self, event):
        if(self.Has_Flag(mfs.CAN_DELETE)):
            self.deleteLater()
        elif(self.Has_Flag(mfs.CAN_HIDE)):
            self.hide()