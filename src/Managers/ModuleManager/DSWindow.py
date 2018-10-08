from PyQt5.Qt import *
import json as json

class DSWindow(QMainWindow):

############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################
    
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
        event.accept()

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