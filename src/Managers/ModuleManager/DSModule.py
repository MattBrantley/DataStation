from PyQt5.Qt import *
import time, os, json
from src.Constants import moduleFlags as mfs
from src.Managers.ModuleManager.ModuleResource import *

class DSModule(QDockWidget):
    Module_Name = 'Default'
    Module_Flags = []
    
############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################
    def Get_Window(self):
        return self.window

    def Get_Name(self):
        return self.Module_Name

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

    def Get_Resources(self, type=-1, tags=[]):
        return self.getResources(type, tags)

    def Add_Arbitrary_Data_Resource(self, name, tags=[], data=None):
        self.addArbitraryDataResource(name, tags, data)

    def Add_Measurement_Packet_Resource(self, name, tags=[], measurementPacket=None):
        self.addMeasurementPacketResource(name, tags, measurementPacket)

    def Remove_Resource(self, resourceObject):
        self.removeResource(resourceObject)

    def Remove_All_Resources(self):
        self.removeAllResources()

############################################################################################
#################################### INTERNAL USER ONLY ####################################
    def __init__(self, ds, handler):
        super().__init__()
        self.ds = ds
        self.handler = handler
        self.resourceList = list()
        self.modDataPath = os.path.join(os.path.join(ds.rootDir, 'Module Data'), self.Module_Name)
        self.modSettingsFolder = os.path.join(self.modDataPath, 'settings')
        self.modSettingsPath = os.path.join(self.modSettingsFolder, self.handler.Get_UUID()+'.json')
        os.makedirs(os.path.dirname(self.modSettingsPath), exist_ok=True)
        self.modSettingsPathSwap = os.path.join(self.modSettingsFolder,  self.handler.Get_UUID()+'.json_swap')

        self.setFeatures(QDockWidget.DockWidgetMovable)

        if(self.Has_Flag(mfs.CAN_DELETE) or self.Has_Flag(mfs.CAN_HIDE)):
            self.setFeatures(self.features() | QDockWidget.DockWidgetClosable)
        if(self.Has_Flag(mfs.CAN_FLOAT)):
            self.setFeatures(self.features() | QDockWidget.DockWidgetFloatable)

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

##### Data Resources #####

    def getResources(self, type, tags):
        outList = list()
        for resource in self.resourceList:
            if(type != -1):
                if(isinstance(resource, type) is False):
                    continue

            if len(tags) != 0:
                if(resource.Has_Tags(tags) is False):
                    continue

            outList.append(resource)

        return outList

    def addArbitraryDataResource(self, name, tags, data):
        newResource = ArbitraryDataResource(self, name, tags, data)
        self.resourceList.append(newResource)
        self.ds.mM.resourceAdded(self, newResource)

    def addMeasurementPacketResource(self, name, tags, measurementPacket):
        newResource = MeasurementPacketResource(self, name, tags, measurementPacket)
        self.resourceList.append(newResource)
        self.ds.mM.resourceAdded(self, newResource)

    def removeResource(self, resourceObject):
        self.resourceList.remove(resourceObject)
        self.ds.mM.resourceRemoved(self)

    def removeAllResources(self):
        self.resourceList = list()
        self.ds.mM.resourceRemoved(self)

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