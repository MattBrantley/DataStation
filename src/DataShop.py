import sys, uuid, pickle, numpy as np, sqlite3, os, matplotlib.pyplot as plt, random, psutil, imp, multiprocessing, copy, queue, json, DSUnits
from pathlib import Path
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d import proj3d
from xml.dom.minidom import *
from xml.etree.ElementTree import *
from PyQt5.QtCore import Qt, QVariant, QTimer, QSize
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
#from PyQt5 import QtWidgets
from UserScriptsController import *
from UserScript import *
from Constants import DSConstants as DSConstants
# NOTES FOR FUTURE INSTALLS
# pyqtgraph has an import warning that is solved by running "conda install h5py==2.8.0"

import DSUnits, DSPrefix
from DSWorkspace import DSWorkspace
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

sys._excepthook = sys.excepthook

def default_exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)

sys.excepthook = default_exception_hook

class mainWindow(QMainWindow):
    logDetail = DSConstants.LOG_PRIORITY_MED

    def __init__(self, app):
        super().__init__()
        self.app = app

        # All used widgets need to be registered here - they autopopulate into the menu.
        # Also, ensure the widget is imported in the import statements above.
        # Generate a widget instance in initUI()
        self.setGeometry(300, 300, 640, 480)
        self.setWindowTitle('DataShop (Alpha) - Loading...')

        self.logDockWidget = logDockWidget(self)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.logDockWidget)
        self.show()
        app.processEvents()

        self.processWidget = processWidget(self)
        self.workspace = DSWorkspace(self)

        self.workspaceTreeDockWidget = workspaceTreeDockWidget(self)
        self.settingsDockWidget = settingsDockWidget(self)
        self.inspectorDockWidget = inspectorDockWidget(self)
        self.editorWidget = editorWidget(self)
        self.sequencerDockWidget = sequencerDockWidget(self)
        self.instrumentWidget = instrumentWidget(self, self.workspace.DSInstrumentManager)
        self.workspace.DSInstrumentManager.instrumentWidget = self.instrumentWidget #HOTFIX - Order of Execution Issue... NOT PRETTY

        self.workspace.workspaceTreeWidget = self.workspaceTreeDockWidget.workspaceTreeWidget

        self.initActions()
        self.loginWindow = loginDockWidget(self)
        self.initUI()
        self.postLog('Data Station Finished Loading!', DSConstants.LOG_PRIORITY_HIGH)

    def updateState(self, state):
        if(state == DSConstants.MW_STATE_NO_WORKSPACE):
            self.exitAction.setEnabled(True)
            self.newAction.setEnabled(True)
            self.saveAction.setEnabled(False)
            self.openAction.setEnabled(True)
            self.settingsAction.setEnabled(False)
            self.importAction.setEnabled(False)
            self.importMenu.setEnabled(False)
            self.workspaceTreeDockWidget.workspaceTreeWidget.setAcceptDrops(False)
        elif(state == DSConstants.MW_STATE_WORKSPACE_LOADED):
            self.exitAction.setEnabled(True)
            self.newAction.setEnabled(True)
            self.saveAction.setEnabled(True)
            self.openAction.setEnabled(True)
            self.settingsAction.setEnabled(False)
            self.importAction.setEnabled(True)
            self.importMenu.setEnabled(True)
            self.workspaceTreeDockWidget.workspaceTreeWidget.setAcceptDrops(True)
        else:
            self.exitAction.setEnabled(False)
            self.newAction.setEnabled(False)
            self.saveAction.setEnabled(False)
            self.openAction.setEnabled(False)
            self.settingsAction.setEnabled(False)
            self.importAction.setEnabled(False)
            self.importMenu.setEnabled(False)
            self.workspaceTreeDockWidget.workspaceTreeWidget.setAcceptDrops(False)

    def initActions(self):
        dir = os.path.dirname(__file__)

        self.exitAction = QAction(QIcon(os.path.join(dir, 'icons2\minimize.png')), 'Exit', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.setStatusTip('Exit Application')
        self.exitAction.triggered.connect(self.close)

        self.newAction = QAction(QIcon(os.path.join(dir, 'icons2\controller.png')), 'New Workspace', self)
        self.newAction.setShortcut('Ctrl+N')
        self.newAction.setStatusTip('Create a New Workspace')
        self.newAction.triggered.connect(self.workspace.newWorkspace)

        self.saveAction = QAction(QIcon(os.path.join(dir, 'icons2\save.png')), 'Save Workspace As..', self)
        self.saveAction.setShortcut('Ctrl+S')
        self.saveAction.setStatusTip('Save Workspace As..')
        self.saveAction.triggered.connect(self.workspace.saveWSToNewSql)

        self.openAction = QAction(QIcon(os.path.join(dir, 'icons2\\folder.png')), 'Open Workspace', self)
        self.openAction.setShortcut('Ctrl+O')
        self.openAction.setStatusTip('Open Workspace')
        self.openAction.triggered.connect(self.workspace.loadWSFromSql)

        self.settingsAction = QAction(QIcon(os.path.join(dir, 'icons2\settings.png')), 'Settings', self)
        self.settingsAction.setShortcut('Ctrl+S')
        self.settingsAction.setStatusTip('Adjust Settings')

        self.importAction = QAction(QIcon(os.path.join(dir, 'icons2\pendrive.png')), 'Import', self)
        self.importAction.setStatusTip('Import Data')
        self.importAction.triggered.connect(self.workspace.importData)

        self.viewWindowsAction = QAction('Import', self)
        self.viewWindowsAction.triggered.connect(self.populateViewWindowMenu)

    def initUI(self):
        self.initMenu()
        self.initToolbar()
        self.updateState(DSConstants.MW_STATE_NO_WORKSPACE)
        
        self.newsWidget = newsWidget(self)
        self.setCentralWidget(self.newsWidget)
        self.statusBar()

        self.addDockWidget(Qt.LeftDockWidgetArea, self.workspaceTreeDockWidget)

        self.addDockWidget(Qt.RightDockWidgetArea, self.processWidget)

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

        self.AnimatedDocks = True
        self.setDockNestingEnabled(True)

        self.setGeometry(300, 300, 1280, 720)
        self.setWindowTitle('DataShop (Alpha)')
        self.show()

    def postLog(self, text, level, **kwargs):
        if(self.logDetail >= level):
            self.logDockWidget.postLog(text, **kwargs)
            print(text)
            app.processEvents()

    def populateViewWindowMenu(self):
        windows = self.findChildren(QDockWidget)
        self.viewWindowsMenu.clear()
        for window in windows:
            if(hasattr(window, 'doNotAutoPopulate') is False):
                action = QAction(str(window.windowTitle()), self)
                action.setCheckable(True)
                action.setChecked(window.isVisible())
                #self.workspace.to
                if(window.isVisible()):
                    action.triggered.connect(window.hide)
                else:
                    action.triggered.connect(window.show)

                self.viewWindowsMenu.addAction(action)

    def initMenu(self):
        self.menubar = self.menuBar()
        self.fileMenu = self.menubar.addMenu('&File')
        self.fileMenu.addAction(self.newAction)
        self.fileMenu.addAction(self.saveAction)
        self.fileMenu.addAction(self.openAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.settingsAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.importAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAction)

        self.viewWindowsMenu = QMenu('Windows')
        self.viewWindowsMenu.aboutToShow.connect(self.populateViewWindowMenu)

        self.viewMenu = self.menubar.addMenu('&View')
        self.viewMenu.addMenu(self.viewWindowsMenu)

        self.importMenu = self.menubar.addMenu('&Import')
        self.workspace.userScripts.populateImportMenu(self.importMenu, self)

    def initToolbar(self):
        self.toolbar = self.addToolBar('Toolbar')
        self.toolbar.addAction(self.newAction)
        self.toolbar.addAction(self.saveAction)
        self.toolbar.addAction(self.openAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.settingsAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.importAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.exitAction)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mW = mainWindow(app)
    try:
        sys.exit(app.exec_())
    except:
        mW.postLog("Exiting!", DSConstants.LOG_PRIORITY_HIGH)

