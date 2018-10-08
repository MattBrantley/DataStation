import sys, uuid, pickle, numpy as np, sqlite3, os, matplotlib.pyplot as plt, random, psutil, imp, multiprocessing, copy, queue, json
from pathlib import Path
from xml.dom.minidom import *
from xml.etree.ElementTree import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
# NOTES FOR FUTURE INSTALLS
# pyqtgraph has an import warning that is solved by running "conda install h5py==2.8.0"
# nidaqmx - pip install nidaqmx
# nifgen - pip install nifgen
# niscope - pip install niscope
# proctitle - pip install setproctitle -- NOT USED?
# pyserial - pip install pyserial
# pyqt5 version updated "pip install pyqt5"
#   -> Caused issues with matplotlib fixed with "pip install matplotlib --upgrade"
#   -> Downgraded to pyqt5 v 5.10.1 with "pip install pyqt5==5.10.1 --user"
# pyqtchart - pip install pyqtchart --user
#   -> Had to redowngrade to 5.10.1
#   -> Downgraded pyqtchart to 5.10.1
# labview runtime is automatically polled and link provided - thanks NI!


# --- In case of bug: break glass! ---
#import traceback
#traceback.print_stack() 
# ---                              ---

def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn

from src.Constants import DSConstants as DSConstants
from src.Managers.WorkspaceManager.WorkspaceManager import WorkspaceManager, DSUnits, DSPrefix
from src.Managers.InstrumentManager.InstrumentManager import InstrumentManager
from src.Managers.HardwareManager.HardwareManager import HardwareManager
from src.Managers.ModuleManager.ModuleManager import ModuleManager

sys._excepthook = sys.excepthook

def default_exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)

sys.excepthook = default_exception_hook

class DataStation_Core(QObject):
    logDetail = DSConstants.LOG_PRIORITY_MED

############################################################################################
##################################### EXTERNAL SIGNALS #####################################
    
##### Signals: DataStation States #####
    DataStation_Loaded = pyqtSignal()
    DataStation_Closing = pyqtSignal()
    DataStation_Closing_Final = pyqtSignal()

##### Signals: Logs #####
    Log_Posted = pyqtSignal(str) # text

############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.DSC = DSConstants()
        self.rootDir = os.path.dirname(__file__)
        self.srcDir = os.path.join(self.rootDir, 'src')
        self.ssDir = os.path.join(self.rootDir, 'Stylesheets')

        self.setAppIcons()
        self.initManagers()
        self.hM.loadHardwareState()
        self.postLog('Waiting on User Profile selection..', DSConstants.LOG_PRIORITY_HIGH)

        self.wM.loadPreviousWS()
        self.iM.loadPreviousInstrument()
        self.iM.loadPreviousSequence()

        self.DataStation_Loaded.emit()
        self.postLog('Data Station Finished Loading!', DSConstants.LOG_PRIORITY_HIGH)

    def setAppIcons(self):
        self.app_icon = QIcon()
        self.app_icon.addFile(os.path.join(self.srcDir, r'DSIcons\DataStation_Small_16.png'), QSize(16,16))
        self.app_icon.addFile(os.path.join(self.srcDir, r'DSIcons\DataStation_Small_24.png'), QSize(24,24))
        self.app_icon.addFile(os.path.join(self.srcDir, r'DSIcons\DataStation_Small_32.png'), QSize(32,32))
        self.app_icon.addFile(os.path.join(self.srcDir, r'DSIcons\DataStation_Small_48.png'), QSize(48,48))
        self.app_icon.addFile(os.path.join(self.srcDir, r'DSIcons\DataStation_Small_256.png'), QSize(256,256))
        self.app.setWindowIcon(self.app_icon)

        self.trayIcon = QSystemTrayIcon(self.app_icon, self)
        self.trayIcon.show()

    def initManagers(self):
        self.mM = ModuleManager(self)           # MODULE MANAGER
        self.mM.DSLoading()
        self.mM.scanModules()                       # LOAD MODULES

        self.wM = WorkspaceManager(self)        # WORKSPACE CONTROLLER
        self.wM.initUserScriptController()          # USER SCRIPTS
        self.wM.initDatabaseCommManager()           # DATABASE COMM

        self.iM = InstrumentManager(self)       # INSTRUMENT MANAGER
        self.iM.loadComponents()                    # USER COMPONENTS

        self.hM = HardwareManager(self)         # HARDWARE MANAGER
        self.hM.loadFilters()                       # USER FILTERS
        self.hM.loadHardwareDrivers()               # HARDWARE DRIVERS
        self.hM.loadLabviewInterface()              # LABVIEW INTERFACE

        self.wM.connections(self.iM, self.hM)
        self.iM.connections(self.wM, self.hM)
        self.hM.connections(self.wM, self.iM)
        self.mM.connections(self.wM, self.hM, self.iM)

    #def finishInitWithUser(self, userData):
        #self.postLog('User Profile Selected: ' + userData['First Name'] + ' ' + userData['Last Name'], DSConstants.LOG_PRIORITY_HIGH)
        #self.wM.userProfile = userData

        #self.setGeometry(300, 300, 1280, 720)
        #self.setWindowTitle('DataStation (Alpha)')
        #self.show()
        #self.restoreWindowStates()

    #def initActions(self):
    #    self.exitAction = QAction(QIcon(os.path.join(self.srcDir, r'icons2\minimize.png')), 'Exit', self)
    #    self.exitAction.setShortcut('Ctrl+Q')
    #    self.exitAction.setStatusTip('Exit Application')
    #    self.exitAction.triggered.connect(self.close)

    #def initMenu(self):
    #    self.menubar = self.menuBar()
    #    self.fileMenu = self.menubar.addMenu('&File')
    #    self.fileMenu.addSeparator()
    #    self.fileMenu.addAction(self.exitAction)

        #self.viewWindowsMenu = QMenu('Windows')
        #self.viewWindowsMenu.aboutToShow.connect(self.populateViewWindowMenu)

        #self.viewMenu = self.menubar.addMenu('&View')
        #self.viewMenu.addMenu(self.viewWindowsMenu)

        #self.moduleManagerMenu = self.menubar.addMenu(self.mM.populateMenu())

    #def populateViewWindowMenu(self):
    #    windows = self.findChildren(QDockWidget)
    #    self.viewWindowsMenu.clear()
    #    for window in windows:
    #        if(hasattr(window, 'doNotAutoPopulate') is False):
    #            action = QAction(str(window.windowTitle()), self)
    #            action.setCheckable(True)
    #            action.setChecked(window.isVisible())##

    #            if(window.isVisible()):
    #                action.triggered.connect(window.hide)
    #            else:
    #                action.triggered.connect(window.show)

    #            self.viewWindowsMenu.addAction(action)

    def postLog(self, key, level, **kwargs):
        useKey = kwargs.get('textKey', False)
        if(useKey):
            text = self.DSC.getLogText(key)
        else:
            text = key

        if(self.logDetail >= level):
            #self.logDockWidget.postLog(text, **kwargs)
            self.Log_Posted.emit(text)
            #print(text)
            app.processEvents()

    def softExit(self):
        self.postLog('Shutting down Datastation!', DSConstants.LOG_PRIORITY_HIGH)
        self.trayIcon.hide()
        self.DataStation_Closing.emit()
        self.DataStation_Closing_Final.emit()

    def signalClose(self):
        self.close()

    def closeEvent(self, event):
        self.softExit()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    core = DataStation_Core(app)
    try:
        sys.exit(app.exec_())
    except:
        core.postLog("Datastation successfully closed!", DSConstants.LOG_PRIORITY_HIGH)

 