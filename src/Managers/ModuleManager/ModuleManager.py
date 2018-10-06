import os, sys, imp, time, inspect, json as json
from src.Constants import DSConstants as DSConstants
from src.Constants import readyCheckPacket
from src.Managers.ModuleManager.DSModule import DSModule
from src.Managers.ModuleManager.moduleManagerWindow import moduleManagerWindow
from src.Managers.ModuleManager.DSWindow import DSWindow
from src.Managers.ModuleManager.ModuleHandler import ModuleHandler
import json as json
from PyQt5.Qt import *

class ModuleManager(QObject):

############################################################################################
##################################### EXTERNAL SIGNALS #####################################
    


############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################

    ##### Modules #####
    def Get_Available_Modules(self):
        return self.modulesAvailable

    def Scan_Modules(self):
        self.scanModules()

    def Add_Module_Instance(self, module, window):
        self.addModuleInstance(module, window)

    ##### Windows #####
    def Add_New_Window(self):
        self.addWindow()

    def Get_Windows(self):
        return self.mainWindows

############################################################################################
#################################### INTERNAL USER ONLY ####################################

    def __init__(self, mW):
        super().__init__()
        self.mW = mW
        self.moduleDir = os.path.join(self.mW.rootDir, 'Modules')
        self.modulesAvailable = list()
        self.modules = list()
        self.mainWindows = list()

        self.mW.DataStation_Closing.connect(self.DSClosing)

##### DataStation Reserved Functions #####

    def connections(self, wM, hM, iM):
        self.wM = wM
        self.hM = hM
        self.iM = iM
        self.initModuleSettingsWindow()
        # Called after all managers are created so they can connect to each other's signals

    def DSClosing(self):
        for window in self.mainWindows:
            window.close()
        print('Module Manager Closing')

##### Module Manager Settings Window #####

    def initModuleSettingsWindow(self):
        self.moduleSettingsWindow = moduleManagerWindow(self.mW)
        self.moduleSettingsWindow.show()

##### Windows #####

    def addWindow(self):
        newWindow = DSWindow(self.mW)
        newWindow.setWindowTitle('DataStation Expansion Window #' + str(len(self.mainWindows)+1))
        self.mainWindows.append(newWindow)

##### Modules #####

    def addModuleInstance(self, module, window):
        modHandler = ModuleHandler(module, window, self.mW)
        self.modules.append(modHandler)

    def scanModules(self):
        self.modulesAvailable = list()
        self.mW.postLog('Searching For Modules... ', DSConstants.LOG_PRIORITY_HIGH)

        for root, dirs, files in os.walk(self.moduleDir):
            for name in files:
                url = os.path.join(root, name)
                res = self.verifyModule(url)
                if(res is not False):
                    nMod = ModuleAvailable(self.moduleDir, name, url, res)
                    self.modulesAvailable.append(nMod)
                    self.mW.postLog('   Found Module: ' + name, DSConstants.LOG_PRIORITY_HIGH)

        self.mW.postLog('Finished Searching For Modules!', DSConstants.LOG_PRIORITY_HIGH)

    def verifyModule(self, url):
        mod_name, file_ext = os.path.splitext(os.path.split(url)[-1])

        if file_ext.lower() == '.py':
            py_mod = imp.load_source(mod_name, url)
        else:
            return False

        if py_mod != None:
            if(hasattr(py_mod, mod_name) is True):
                module = getattr(py_mod, mod_name)
                if(issubclass(module, DSModule)):
                    return module
                else:
                    return False
            else:
                return False
        else:
            return False

        return False

class ModuleDirectory():
    def __init__(self, dirStructure, folderName, folderPath):
        self.folderNmae = folderName
        self.folderPath = folderPath
        self.childModules = list()
        self.childDirectories = list()

class ModuleAvailable():
    def __init__(self, moduleDir, fileName, filePath, modClass):
        self.moduleDir = moduleDir
        self.fileName = fileName
        self.filePath = filePath
        self.modClass = modClass
        self.subDirectories = list()

        if hasattr(modClass, 'Module_Name'):
            self.name = getattr(modClass, 'Module_Name')
        else:
            self.name = 'NULL'
        
        if hasattr(modClass, 'Module_Flags'):
            self.modFlags = getattr(modClass, 'Module_Flags')
        else:
            self.modFlags = list()

        self.parseDirectories()

    def parseDirectories(self):
        relPath = os.path.relpath(self.filePath, start=self.moduleDir)
        while os.path.dirname(relPath) != '':
            relPath = os.path.dirname(relPath)
            relPathBase = os.path.basename(relPath)
            self.subDirectories.append(relPathBase)
        self.subDirectories.reverse()
