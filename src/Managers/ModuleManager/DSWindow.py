from PyQt5.Qt import *
import json as json

class DSWindow(QMainWindow):

############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################
    
    def Widget_Closing(self, widget):
        pass

############################################################################################
#################################### INTERNAL USER ONLY ####################################
    def __init__(self, core):
        super().__init__()
        self.moduleHandlers = list()
        self.core = core
        self.mM = core.mM
        self.AnimatedDocks = True
        self.setDockNestingEnabled(True)
        self.initMenu()
        self.setGeometry(300, 300, 1280, 720)
        self.show()

##### DataStation Reserverd #####
    def closeEvent(self, event):
        if(self.mM.isShutdown is False):
            menu = QMenu()

            removeMenu = QAction('Remove Window From Workspace')
            removeMenu.triggered.connect(self.removeWindow)
            shutDownMenu = QAction("Shut Down DataStation")
            shutDownMenu.triggered.connect(self.closeDataStation)
            menu.addAction(removeMenu)
            menu.addAction(shutDownMenu)

            action = menu.exec_(QCursor().pos())
            if(action is None):
                event.ignore()
                return

        event.accept()
        
    def removeWindow(self):
        self.mM.Close_Window(self)
        #event.accept()

    def closeDataStation(self):
        self.mM.Close_DataStation(self)
        #event.accept()


##### Modules #####
    def transferModule(self, moduleHandler):
        self.moduleHandlers.append(moduleHandler)
        self.addDockWidget(Qt.LeftDockWidgetArea, moduleHandler.modInstance)

##### Window State Info #####
    def saveWindowState(self):
        stateDict = dict()
        stateDict['state'] = json.dumps(bytes(self.saveState().toHex()).decode('ascii'))
        stateDict['geometry'] = json.dumps(bytes(self.saveGeometry().toHex()).decode('ascii'))
        stateDict['modules'] = self.serializeModuleList()
        
        return stateDict

    def loadWindowState(self, data):
        tempGeometry = QByteArray.fromHex(bytes(json.loads(data['geometry']), 'ascii'))
        self.restoreGeometry(tempGeometry)
        tempState = QByteArray.fromHex(bytes(json.loads(data['state']), 'ascii'))
        self.restoreState(tempState)

    def serializeModuleList(self):
        moduleSerialList = list()
        for moduleHandler in self.moduleHandlers:
            modData = {'uuid': moduleHandler.uuid, 'filePath': moduleHandler.modObject.filePath}
            moduleSerialList.append(modData)
        return moduleSerialList

##### Window Configuration #####
    def centerWindow(self):
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def initMenu(self):
        self.menubar = self.menuBar()
        self.fileMenu = self.menubar.addMenu('&File')
        self.fileMenu.addSeparator()
        #self.fileMenu.addAction(self.exitAction)

        #self.viewWindowsMenu = QMenu('Windows')
        #self.viewWindowsMenu.aboutToShow.connect(self.populateViewWindowMenu)

        #self.viewMenu = self.menubar.addMenu('&View')
        #self.viewMenu.addMenu(self.viewWindowsMenu)

        self.moduleManagerMenu = self.menubar.addMenu(self.mM.Get_Manager_Menu())

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