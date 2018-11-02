from PyQt5.Qt import *
import time, os, json
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

    def Write_Setting(self, key, value):
        self.writeSetting(key, value)

    def Read_Setting(self, key):
        return self.readSetting(key)

    def Get_Handler(self):
        return self.handler

############################################################################################
#################################### INTERNAL USER ONLY ####################################
    def __init__(self, ds, handler):
        super().__init__()
        self.ds = ds
        self.handler = handler
        self.modDataPath = os.path.join(os.path.join(ds.rootDir, 'Module Data'), self.Module_Name)
        self.modSettingsFolder = os.path.join(self.modDataPath, 'settings')
        self.modSettingsPath = os.path.join(self.modSettingsFolder, self.handler.Get_UUID()+'.json')
        os.makedirs(os.path.dirname(self.modSettingsPath), exist_ok=True)
        self.modSettingsPathSwap = os.path.join(self.modSettingsFolder,  self.handler.Get_UUID()+'.json_swap')

        self.setFeatures(QDockWidget.DockWidgetMovable)
        #self.setFeatures(QDockWidget.AllDockWidgetFeatures)

        if(self.Has_Flag(mfs.CAN_DELETE) or self.Has_Flag(mfs.CAN_HIDE)):
            self.setFeatures(self.features() | QDockWidget.DockWidgetClosable)
        #if(self.Has_Flag(mfs.CAN_FLOAT)):
        self.setFeatures(self.features() | QDockWidget.DockWidgetFloatable)

        #self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint)

        #self.visibilityChanged.connect(self.visibilityModified)

        url = os.path.join(self.ds.srcDir, 'icons5/zoom-in.png')

        self.setStyleSheet('QDockWidget::close-button {image: url(' + url + ');}')

    def onDataStationClose(self):
        pass

    def visibilityModified(self, visible):
        if self.isVisible() and self.isHidden():
            self.Get_Handler().removeHandler()
            self.deleteLater()

    def configureWidget(self, window):
        pass #OVewrride this

    def closeEvent(self, event):
        if(self.Has_Flag(mfs.CAN_DELETE)):
            self.Get_Handler().removeHandler()
            self.deleteLater()
        elif(self.Has_Flag(mfs.CAN_HIDE)):
            self.hide()

##### Settings File #####

    def writeSetting(self, key, value):
        try:
            if(os.path.isfile(self.modSettingsPath)):
                with open(self.modSettingsPath, 'r') as file:
                    settingsDict = json.load(file)
                    if(isinstance(settingsDict, dict)):
                        settingsDict[key] = value
                    else:
                        settingsDict = dict()
                        settingsDict[key] = value
                    with open(self.modSettingsPathSwap, 'w') as file_swap:
                        json.dump(settingsDict, file_swap, sort_keys=True, indent=4)

                if(os.path.isfile(self.modSettingsPathSwap)):
                    os.replace(self.modSettingsPathSwap, self.modSettingsPath)

            else:
                with open(self.modSettingsPath, 'w') as file:
                    settingsDict = dict()
                    settingsDict[key] = value
                    json.dump(settingsDict, file, sort_keys=True, indent=4)
        except:
            print('ERROR WRITING SETTINGS')

    def readSetting(self, key):
        try:
            with open(self.modSettingsPath, 'r') as file:
                settingsDict = json.load(file)
                return settingsDict[key]
        except:
            return None