import sys, uuid, pickle, numpy as np, sqlite3, os, matplotlib.pyplot as plt, random, psutil, imp, multiprocessing, copy, queue, json, time
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
from src.Constants import logObject
from src.Managers.WorkspaceManager.WorkspaceManager import WorkspaceManager
from src.Managers.InstrumentManager.InstrumentManager import InstrumentManager
from src.Managers.HardwareManager.HardwareManager import HardwareManager
from src.Managers.ModuleManager.ModuleManager import ModuleManager

sys._excepthook = sys.excepthook

def default_exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)

sys.excepthook = default_exception_hook

class DataStation_Core(QMainWindow):

############################################################################################
##################################### EXTERNAL SIGNALS #####################################
    
##### Signals: DataStation States #####
    DataStation_Loaded = pyqtSignal()
    DataStation_Closing = pyqtSignal()
    DataStation_Closing_Final = pyqtSignal()

##### Signals: Logs #####
    Log_Posted = pyqtSignal(object) # Log Object

############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.DSC = DSConstants()
        self.rootDir = os.path.dirname(__file__)
        self.srcDir = os.path.join(self.rootDir, 'src')
        self.ssDir = os.path.join(self.rootDir, 'Stylesheets')
        self.logText = list()

        self.setAppIcons()
        self.initManagers()
        self.initTrayMenu()

        self.DataStation_Loaded.emit()
        self.app.lastWindowClosed.connect(self.lastWindowClosed)

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

    def initTrayMenu(self): 
        self.trayMenu = QMenu()
        self.exitAction = QAction('Shutdown DataStation')
        self.exitAction.triggered.connect(self.softExit)

        self.trayMenu.addAction(self.exitAction)
        self.trayMenu.addSeparator()

        self.trayIcon.setContextMenu(self.trayMenu)

    def initManagers(self):
        self.mM = ModuleManager(self)           # MODULE MANAGER
        self.wM = WorkspaceManager(self)        # WORKSPACE CONTROLLER
        self.iM = InstrumentManager(self)       # INSTRUMENT MANAGER
        self.hM = HardwareManager(self)         # HARDWARE MANAGER

        self.wM.connections()
        self.iM.connections()
        self.hM.connections()
        self.mM.connections()

    def postLog(self, key, level, source=None, **kwargs):
        useKey = kwargs.get('textKey', False)
        if(useKey):
            text = self.DSC.getLogText(key)
        else:
            text = key

        log = logObject(source, text, level)

        self.Log_Posted.emit(log)
        self.logText.append(log)
        app.processEvents()

    def softExit(self):
        self.postLog('Shutting down Datastation!', DSConstants.LOG_PRIORITY_HIGH)
        self.mM.isShutdown = True
        self.trayIcon.hide()
        self.DataStation_Closing.emit()
        self.DataStation_Closing_Final.emit()
        self.app.processEvents()
        self.app.quit()

    def lastWindowClosed(self):
        self.trayIcon.showMessage('DataStation Still Running!', 'All windows were closed but DataStation is still running in the background!', QSystemTrayIcon.Information)

    def closeEvent(self, event):
        self.softExit()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    core = DataStation_Core(app)
    try:
        sys.exit(app.exec_())
    except:
        core.postLog("Datastation successfully closed!", DSConstants.LOG_PRIORITY_HIGH)

