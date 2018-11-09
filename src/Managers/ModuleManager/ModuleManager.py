import os, sys, imp, time, inspect, json as json, uuid
from src.Constants import DSConstants as DSConstants
from src.Constants import readyCheckPacket
from src.Managers.ModuleManager.DSModule import DSModule
from src.Managers.ModuleManager.moduleManagerWindow import moduleManagerWindow
from src.Managers.ModuleManager.DSWindow import DSWindow
from src.Managers.ModuleManager.ModuleHandler import ModuleHandler
from src.Managers.ModuleManager.mainWindow import mainWindow
from PyQt5.Qt import *

class ModuleManager(QObject):
    
############################################################################################
##################################### EXTERNAL SIGNALS #####################################

##### Signals: Windows #####
    Window_Added = pyqtSignal(object) # Window
    Window_Removed = pyqtSignal(object) # Window

##### Signals: Modules #####
    Module_Instantiated = pyqtSignal(object) # Module
    Module_Deleted = pyqtSignal(object) # Module
    Module_Transfered_To_Window = pyqtSignal(object, object) # Module, Window

############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################
    
    def Close_Window(self, window):
        self.windowClosing(window)

    def Close_DataStation(self, window):
        self.closeDataStation(window)

    def Save_Window_States(self):
        return self.saveWindowStates()

    def Load_Window_States(self, data):
        self.loadWindowStates(data)

    def Hide_Main_Window(self):
        self.hideMainWindow()

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

    def Get_Module_Instances(self):
        return self.modules

    def Add_Module_Instance(self, module, window, uuid=str(uuid.uuid4())):
        self.addModuleInstance(module, window, uuid)

    def Remove_Module_Instance(self, moduleHandler):
        self.removeModuleInstance(moduleHandler)

    def Get_Module_Resources(self, module=-1, types=[], tags=[]):
        self.getModuleResources(module, tags)

    ##### Windows #####
    def Add_New_Window(self):
        self.addWindow()

    def Get_Windows(self):
        return self.mainWindows

    def Set_StyleSheet(self, path):
        self.setStylesheet(path)

    def Get_StyleSheet(self):
        return self.styleSheet

############################################################################################
#################################### INTERNAL USER ONLY ####################################
    def __init__(self, ds):
        super().__init__()
        self.ds = ds
        self.moduleDir = os.path.join(self.ds.rootDir, 'Modules')
        self.styleSheet = ''
        self.modulesAvailable = list()
        self.modules = list()
        self.mainWindows = list()
        self.isShutdown = False
        self.defaultModules = ['Default Loading Screen', 'Profile Selection']
        url = os.path.join(self.ds.srcDir, 'icons5/zoom-in.png')
        #self.defaultSS = 'QDockWidget::close-button {image: url(' + url + ');}'
        self.defaultSS = 'QPushButton {color:#b1b1b1; }'

        self.focusLock = False

        self.populateMenu()
        self.scanModules()
        self.DSLoading()

        self.ds.DataStation_Closing.connect(self.DSClosing)
        self.ds.DataStation_Closing_Final.connect(self.DSLateClosing)
        self.ds.app.focusWindowChanged.connect(self.focusWindowChanged)

##### DataStation Reserved Functions #####
    def connections(self):
        self.wM = self.ds.wM
        self.hM = self.ds.hM
        self.iM = self.ds.iM
        self.initModuleSettingsWindow()

    def DSLoading(self):
        self.mainWindow = mainWindow(self.ds)
        self.mainWindow.setStyleSheet(self.styleSheet)

        for modName in self.defaultModules:
            widget = self.getModByModName(modName)
            if(widget is not None):
                self.Add_Module_Instance(widget, self.mainWindow, uuid='')

        self.mainWindow.centerWindow()

    def DSLoaded(self):
        pass

    def DSClosing(self):
        for window in self.mainWindows:
            window.close()

    def DSLateClosing(self):
        pass
        #for modHandler in self.modules:
        #    modHandler.removeHandler(late=True)
        #for window in self.mainWindows:
        #    window.close()

    def closeDataStation(self, window):
        self.isShutdown = True
        self.ds.softExit()

    def populateMenu(self):
        self.showWidgetAction = QAction('Show Module Widget')
        self.showWidgetAction.triggered.connect(self.Show_Manager_Widget)

        self.lockFocusAction = QAction('Shared Window Focus', checkable=True)
        self.lockFocusAction.setChecked(True)

        self.menu = QMenu('Modules')
        self.menu.addAction(self.showWidgetAction)
        self.menu.addAction(self.lockFocusAction)

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
            if path is None:
                self.styleSheet = ''
            else:
                with open(path) as file:
                    ssTxt = file.read()
                    self.styleSheet = ssTxt

            for window in self.mainWindows:
                window.setStyleSheet(self.styleSheet + self.defaultSS)
        except:
            self.ds.postLog('Could not load styleSheet: ' + path, DSConstants.LOG_PRIORITY_HIGH)

##### Windows #####
    def hideMainWindow(self):
        self.mainWindow.hide()

    def addWindow(self):
        newWindow = DSWindow(self.ds)
        newWindow.setWindowTitle('DataStation Expansion Window #' + str(len(self.mainWindows)+1))
        newWindow.setStyleSheet(self.styleSheet)
        self.mainWindows.append(newWindow)
        return newWindow

    def windowClosing(self, window):
        self.mainWindows.remove(window)
        self.Window_Removed.emit(window)

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
        
        if(len(self.mainWindows) == 0):
            self.addWindow()

    def focusWindowChanged(self, window):
        if self.focusLock is False:
            self.focusLock = True
            if self.lockFocusAction.isChecked():
                for window in self.mainWindows:
                    window.show()
                    window.raise_()

            self.focusLock = False

##### Modules #####
    def addModuleInstance(self, module, window, uuid):
        modHandler = ModuleHandler(module, window, self.ds, self, uuid)
        self.modules.append(modHandler)

    def removeModuleInstance(self, modHandler):
        self.modules.remove(modHandler)

    def restoreModules(self, modDataList, window):
        for modData in modDataList:
            mod = self.getModByPath(modData['filePath'])
            if mod is not None:
                self.Add_Module_Instance(mod, window, uuid=modData['uuid'])

    def getModByFileName(self, name):
        for mod in self.modulesAvailable:
            if(mod.fileName == name):
                return mod
        return None

    def getModByModName(self, name):
        for mod in self.modulesAvailable:
            if(mod.name == name):
                return mod
        return None

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

        pathStore = sys.path
        sys.path.append(os.path.dirname(url))

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

    def getModuleResources(self, module, types, tags):
        outList = list()
        for moduleIn in self.Get_Module_Instances():
            if module != -1:
                if moduleIn is module:
                    outList.append(moduleIn.Get_Resources(types, tags))
            else:
                outList.append(moduleIn.Get_Resources(types, tags))

        return outList

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
