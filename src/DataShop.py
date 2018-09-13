import sys, uuid, pickle, numpy as np, sqlite3, os, matplotlib.pyplot as plt, random, psutil, imp, multiprocessing, copy, queue, json
from pathlib import Path
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d import proj3d
from xml.dom.minidom import *
from xml.etree.ElementTree import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from Managers.WorkspaceManager import DSUnits, DSPrefix
from Constants import DSConstants as DSConstants
# NOTES FOR FUTURE INSTALLS
# pyqtgraph has an import warning that is solved by running "conda install h5py==2.8.0"
# nidaqmx - pip install nidaqmx
# nifgen - pip install nifgen
# niscope - pip install niscope
# proctitle - pip install setproctitle -- NOT USED?
# pyserial - pip install pyserial
# labview runtime is automatically polled and link provided - thanks NI!


# --- In case of bug: break glass! ---
#import traceback
#traceback.print_stack() 
# ---                              ---

def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn

from Managers.WorkspaceManager.WorkspaceManager import WorkspaceManager
from Managers.InstrumentManager.InstrumentManager import InstrumentManager
from Managers.HardwareManager.HardwareManager import HardwareManager
from DSWidgets.settingsWidget import settingsDockWidget, settingsDefaultImporterListWidget
from DSWidgets.inspectorWidget import inspectorDockWidget
from DSWidgets.workspaceWidget import workspaceTreeDockWidget, WorkspaceTreeWidget
from DSWidgets.logWidget import logDockWidget
from DSWidgets.editorWidget import editorWidget
from DSWidgets.newsWidget import newsWidget
from DSWidgets.sequencerWidget import sequencerDockWidget
from DSWidgets.instrumentWidget import instrumentWidget
from DSWidgets.processWidget import processWidget
from DSWidgets.loginWidget import loginDockWidget
from DSWidgets.hardwareWidget import hardwareWidget
from DSWidgets.controlWidget import controlWidget
from DSWidgets.logoWidget import logoDockWidget

sys._excepthook = sys.excepthook

def default_exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)

sys.excepthook = default_exception_hook

class mainWindow(QMainWindow):
    logDetail = DSConstants.LOG_PRIORITY_MED
    DataStation_Loaded = pyqtSignal()
    DataStation_Closing = pyqtSignal()
    DataStation_Closing_Final = pyqtSignal()

    def center(self):
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.DSC = DSConstants()
        self.srcDir = os.path.dirname(__file__)
        self.rootDir = os.path.dirname(self.srcDir)

        self.loadWindowIcons()
        self.loadingScreenWidgets()
        self.initManagers()
        self.loadWDockWidgets()
        self.initActions()
        self.hM.loadHardwareState()
        self.loginWindow = loginDockWidget(self)
        self.loginWindow.setObjectName('loginWindow')
        self.postLog('Waiting on User Profile selection..', DSConstants.LOG_PRIORITY_HIGH)
        self.loginWindow.runModal() #Open the login window and then waits until it finishes and calls the finishInitWithUser function

        self.wM.connectWidgets() ## THIS NEEDS TO GO BYE BYE

        self.DataStation_Closing.connect(self.updateUserProfile)

    def loadWindowIcons(self):
        self.app_icon = QIcon()
        self.app_icon.addFile(os.path.join(self.srcDir, r'DSIcons\DataStation_Small_16.png'), QSize(16,16))
        self.app_icon.addFile(os.path.join(self.srcDir, r'DSIcons\DataStation_Small_24.png'), QSize(24,24))
        self.app_icon.addFile(os.path.join(self.srcDir, r'DSIcons\DataStation_Small_32.png'), QSize(32,32))
        self.app_icon.addFile(os.path.join(self.srcDir, r'DSIcons\DataStation_Small_48.png'), QSize(48,48))
        self.app_icon.addFile(os.path.join(self.srcDir, r'DSIcons\DataStation_Small_256.png'), QSize(256,256))
        self.app.setWindowIcon(self.app_icon)
        #self.trayIcon = QSystemTrayIcon(self.app_icon, self)
        #self.trayIcon.show()

    def loadingScreenWidgets(self):
        self.setWindowTitle('DataStation (Alpha) - Loading...')

        self.logoDockWidget = logoDockWidget(self)
        self.logoDockWidget.setObjectName('logoDockWidget')
        self.addDockWidget(Qt.TopDockWidgetArea, self.logoDockWidget)
        self.logoDockWidget.setFeatures(QDockWidget.NoDockWidgetFeatures)

        self.logDockWidget = logDockWidget(self)
        self.logDockWidget.setObjectName('logDockWidget')
        self.addDockWidget(Qt.BottomDockWidgetArea, self.logDockWidget)
        self.logDockWidget.setFeatures(QDockWidget.NoDockWidgetFeatures)

        self.show()
        self.center()
        app.processEvents()

    def initManagers(self):
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

    def loadWDockWidgets(self):
        # All used widgets need to be registered here - they autopopulate into the menu.
        # Also, ensure the widget is imported in the import statements above.
        # Generate a widget instance in initUI()
        self.processWidget = processWidget(self)
        self.processWidget.setObjectName('processWidget')

        self.controlWidget = controlWidget(self)
        self.controlWidget.setObjectName('controlWidget')

        self.workspaceTreeDockWidget = workspaceTreeDockWidget(self)
        self.workspaceTreeDockWidget.setObjectName('workspaceTreeDockWidget')

        self.settingsDockWidget = settingsDockWidget(self)
        self.settingsDockWidget.setObjectName('settingsDockWidget')

        self.inspectorDockWidget = inspectorDockWidget(self)
        self.inspectorDockWidget.setObjectName('inspectorDockWidget')

        self.editorWidget = editorWidget(self)
        self.editorWidget.setObjectName('editorWidget')

        self.sequencerDockWidget = sequencerDockWidget(self)
        self.sequencerDockWidget.setObjectName('sequencerDockWidget')

        self.instrumentWidget = instrumentWidget(self)
        self.instrumentWidget.setObjectName('instrumentWidget')

        self.newsWidget = newsWidget(self)
        self.newsWidget.setObjectName('newsWidget')

        self.hardwareWidget = hardwareWidget(self)
        self.hardwareWidget.setObjectName('hardwareWidget')

        self.wM.workspaceTreeWidget = self.workspaceTreeDockWidget.workspaceTreeWidget
        self.wM.workspaceTreeWidget.setObjectName('workspaceTreeWidget')


    def finishInitWithUser(self, userData):
        self.postLog('User Profile Selected: ' + userData['First Name'] + ' ' + userData['Last Name'], DSConstants.LOG_PRIORITY_HIGH)
        self.wM.userProfile = userData
        
        self.initMenu()
        self.statusBar()

        self.logDockWidget.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.removeDockWidget(self.logoDockWidget)

        self.addDockWidget(Qt.TopDockWidgetArea, self.workspaceTreeDockWidget)

        self.addDockWidget(Qt.TopDockWidgetArea, self.newsWidget)

        self.addDockWidget(Qt.TopDockWidgetArea, self.processWidget)

        self.addDockWidget(Qt.BottomDockWidgetArea, self.settingsDockWidget)
        self.settingsDockWidget.setFloating(True)

        self.addDockWidget(Qt.BottomDockWidgetArea, self.inspectorDockWidget)
        self.inspectorDockWidget.setFloating(True)

        self.addDockWidget(Qt.BottomDockWidgetArea, self.sequencerDockWidget)
        self.sequencerDockWidget.setFloating(True)

        self.addDockWidget(Qt.BottomDockWidgetArea, self.editorWidget)
        self.editorWidget.setFloating(True)

        self.addDockWidget(Qt.BottomDockWidgetArea, self.instrumentWidget)
        self.instrumentWidget.setFloating(True)

        self.addDockWidget(Qt.BottomDockWidgetArea, self.hardwareWidget)
        self.hardwareWidget.setFloating(True)

        self.addDockWidget(Qt.BottomDockWidgetArea, self.controlWidget)
        self.controlWidget.setFloating(True)

        self.AnimatedDocks = True
        self.setDockNestingEnabled(True)

        self.setGeometry(300, 300, 1280, 720)
        self.setWindowTitle('DataStation (Alpha)')
        self.show()
        self.restoreWindowStates()
        self.wM.loadPreviousWS()
        self.iM.loadPreviousInstrument()
        self.iM.loadPreviousSequence()

        self.DataStation_Loaded.emit()
        self.postLog('Data Station Finished Loading!', DSConstants.LOG_PRIORITY_HIGH)

    def initActions(self):
        self.exitAction = QAction(QIcon(os.path.join(self.srcDir, r'icons2\minimize.png')), 'Exit', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.setStatusTip('Exit Application')
        self.exitAction.triggered.connect(self.close)

    def initMenu(self):
        self.menubar = self.menuBar()
        self.fileMenu = self.menubar.addMenu('&File')
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAction)

        self.viewWindowsMenu = QMenu('Windows')
        self.viewWindowsMenu.aboutToShow.connect(self.populateViewWindowMenu)

        self.viewMenu = self.menubar.addMenu('&View')
        self.viewMenu.addMenu(self.viewWindowsMenu)

    def populateViewWindowMenu(self):
        windows = self.findChildren(QDockWidget)
        self.viewWindowsMenu.clear()
        for window in windows:
            if(hasattr(window, 'doNotAutoPopulate') is False):
                action = QAction(str(window.windowTitle()), self)
                action.setCheckable(True)
                action.setChecked(window.isVisible())

                if(window.isVisible()):
                    action.triggered.connect(window.hide)
                else:
                    action.triggered.connect(window.show)

                self.viewWindowsMenu.addAction(action)

    def postLog(self, key, level, **kwargs):
        useKey = kwargs.get('textKey', False)
        if(useKey):
            text = self.DSC.getLogText(key)
        else:
            text = key

        if(self.logDetail >= level):
            self.logDockWidget.postLog(text, **kwargs)
            #print(text)
            app.processEvents()

    def updateWindowStates(self):
        windowStates = self.saveState()
        self.wM.userProfile['windowStates'] = json.dumps(bytes(windowStates.toHex()).decode('ascii'))
        windowGeometry = self.saveGeometry()
        self.wM.userProfile['windowGeometry'] = json.dumps(bytes(windowGeometry.toHex()).decode('ascii'))

    def restoreWindowStates(self):
        if('windowGeometry' in self.wM.userProfile):
            tempGeometry = QByteArray.fromHex(bytes(json.loads(self.wM.userProfile['windowGeometry']), 'ascii'))
            self.restoreGeometry(tempGeometry)
        if('windowStates' in self.wM.userProfile):
            tempState = QByteArray.fromHex(bytes(json.loads(self.wM.userProfile['windowStates']), 'ascii'))
            self.restoreState(tempState)

        #These can be restored to show but shouldn't be.
        self.hardwareWidget.filterStackWidget.hide()

    def softExit(self):
        self.postLog('Shutting down Datastation!', DSConstants.LOG_PRIORITY_HIGH)
        #self.trayIcon.hide()
        self.DataStation_Closing.emit()
        self.DataStation_Closing_Final.emit()

    def updateUserProfile(self):
        self.updateWindowStates()
        self.loginWindow.updateUserProfile()

    def signalClose(self):
        self.close()

    def closeEvent(self, event):
        self.softExit()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mW = mainWindow(app)
    try:
        sys.exit(app.exec_())
    except:
        mW.postLog("Datastation successfully closed!", DSConstants.LOG_PRIORITY_HIGH)

