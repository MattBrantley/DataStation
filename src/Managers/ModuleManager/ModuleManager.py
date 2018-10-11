import os, sys, imp, time, inspect, json as json, uuid
from src.Constants import DSConstants as DSConstants
from src.Constants import readyCheckPacket
from src.Managers.ModuleManager.DSModule import DSModule
from src.Managers.ModuleManager.moduleManagerWindow import moduleManagerWindow
from src.Managers.ModuleManager.DSWindow import DSWindow
from src.Managers.ModuleManager.ModuleHandler import ModuleHandler
from src.Managers.ModuleManager.loadingScreenWidget import loadingScreenWidget
from PyQt5.Qt import *

class ModuleManager(QObject):

############################################################################################
##################################### EXTERNAL SIGNALS #####################################
    


############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################

    ##### Manager Widget #####
    def Show_Manager_Widget(self):
        self.showManagerWidget()

    def Get_Manager_Menu(self):
        return self.menu

    ##### Modules #####
    def Get_Available_Modules(self):
        return self.modulesAvailable

    def Scan_Modules(self):
        self.scanModules()

    def Add_Module_Instance(self, module, window, uuid=str(uuid.uuid4())):
        self.addModuleInstance(module, window, uuid)

    ##### Windows #####
    def Add_New_Window(self):
        self.addWindow()

    def Get_Windows(self):
        return self.mainWindows

    def Set_Stylesheet(self, path):
        self.setStylesheet(path)

############################################################################################
#################################### INTERNAL USER ONLY ####################################

    def __init__(self, ds):
        super().__init__()
        self.ds = ds
        self.moduleDir = os.path.join(self.ds.rootDir, 'Modules')
        self.modulesAvailable = list()
        self.modules = list()
        self.mainWindows = list()

        self.populateMenu()

        self.ds.DataStation_Loaded.connect(self.DSLoaded)
        self.ds.DataStation_Closing.connect(self.DSClosing)

##### DataStation Reserved Functions #####

    def connections(self, wM, hM, iM):
        self.wM = wM
        self.hM = hM
        self.iM = iM
        self.initModuleSettingsWindow()
        # Called after all managers are created so they can connect to each other's signals

    def DSLoading(self):
        self.loadScreenWidget = loadingScreenWidget(self.ds)

    def DSLoaded(self):
        self.loadScreenWidget.close()
        tSaveURL = os.path.join(self.ds.srcDir, 'testSave.json')
        if(os.path.isfile(tSaveURL)):
            with open(tSaveURL, 'r+') as file:
                try:
                    windowData = json.load(file)
                    self.loadWindowStates(windowData)
                except:
                    print('ERROR OCCURED LOADING')

    def DSClosing(self):
        tSaveURL = os.path.join(self.ds.srcDir, 'testSave.json')
        with open(tSaveURL, 'w') as file:
            json.dump(self.saveWindowStates(), file, sort_keys=True, indent=4)

        self.closeWindows()

    def populateMenu(self):
        self.showWidgetAction = QAction('Show Module Widget')
        self.showWidgetAction.triggered.connect(self.Show_Manager_Widget)

        self.menu = QMenu('Modules')
        self.menu.addAction(self.showWidgetAction)

        return self.menu

##### Module Manager Settings Window #####

    def initModuleSettingsWindow(self):
        self.moduleSettingsWindow = moduleManagerWindow(self.ds)
        #self.moduleSettingsWindow.show()

    def showManagerWidget(self):
        self.moduleSettingsWindow.show()
        self.moduleSettingsWindow.setWindowState(self.moduleSettingsWindow.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.moduleSettingsWindow.activateWindow()

##### Stylesheets #####

    def setStylesheet(self, path):
        try:
            with open(os.path.join(path)) as file:
                ssTxt = file.read()
                self.setStyleSheet(ssTxt)
        except:
            print('Could not load stylesheet')
        #with open(os.path.join(self.ssDir, 'darkorange.stylesheet')) as file:
        #    ssTxt = file.read()
            #self.setStyleSheet(ssTxt)

##### Windows #####

    def addWindow(self):
        newWindow = DSWindow(self.ds)
        newWindow.setWindowTitle('DataStation Expansion Window #' + str(len(self.mainWindows)+1))
        self.mainWindows.append(newWindow)
        return newWindow

    def closeWindows(self):
        for window in self.mainWindows:
            window.close()

    def saveWindowStates(self):
        windowStates = list()
        for window in self.mainWindows:
            windowStates.append(window.saveWindowState())
        return windowStates

    def loadWindowStates(self, data):
        for window in data:
            newWindow = self.addWindow()
            self.restoreModules(window['modules'], newWindow)
            newWindow.loadWindowState(window)

##### Modules #####

    def addModuleInstance(self, module, window, uuid):
        modHandler = ModuleHandler(module, window, self.ds, uuid)
        self.modules.append(modHandler)

    def restoreModules(self, modDataList, window):
        for modData in modDataList:
            mod = self.getModByPath(modData['filePath'])
            if mod is not None:
                self.Add_Module_Instance(mod, window, uuid=modData['uuid'])

    def getModByPath(self, path):
        for mod in self.modulesAvailable:
            if(mod.filePath == path):
                return mod
        return None

    def scanModules(self):
        self.modulesAvailable = list()
        self.ds.postLog('Searching For Modules... ', DSConstants.LOG_PRIORITY_HIGH)

        for root, dirs, files in os.walk(self.moduleDir):
            for name in files:
                url = os.path.join(root, name)
                res = self.verifyModule(url)
                if(res is not False):
                    nMod = ModuleAvailable(self.moduleDir, name, url, res)
                    self.modulesAvailable.append(nMod)
                    self.ds.postLog('   Found Module: ' + name, DSConstants.LOG_PRIORITY_HIGH)

        self.ds.postLog('Finished Searching For Modules!', DSConstants.LOG_PRIORITY_HIGH)

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
