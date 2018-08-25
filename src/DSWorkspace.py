import os, json, sqlite3, pickle, uuid
from xml.dom.minidom import *
from xml.etree.ElementTree import *
from pathlib import Path
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import multiprocessing
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from UserScriptsController import userScriptsController
from UserScript import *
from InstrumentManager import InstrumentManager
from HardwareManager import HardwareManager
from Constants import DSConstants as DSConstants

class databaseCommManager():
    killMgr = False

    def __init__(self, workspace):
        self.workspace = workspace
        self.mgr = multiprocessing.Manager()
        self.dataQueue = self.mgr.Queue()
        self.responseQueue = self.mgr.Queue()
        self.thread = multiprocessing.Process(group=None, name='Process Worker', target=self.mainLoop, args=(self.workspace.workspaceURL, self.dataQueue, self.responseQueue, ))
        self.thread.daemon = True

    def mainLoop(self, workspaceURL, dataQueue, responseQueue):
        while(True):
            dataSet = dataQueue.get()
            GUID = str(uuid.uuid4().hex)
            GUID = GUID.upper()
            conn = sqlite3.connect(workspaceURL)
            c = conn.cursor()
            c.execute('CREATE TABLE IF NOT EXISTS DataSets (Key INTEGER PRIMARY KEY ASC, Name TEXT NOT NULL, Data Blob, Type TEXT, Units Blob, Prefix Blob, GUID TEXT, timeStamp date);')
            c.execute("INSERT INTO DataSets (Key, Name, Data, GUID, Type, Units, Prefix, timeStamp) VALUES (NULL, ?, ?, ?, ?, ?, ?,  CURRENT_TIMESTAMP);", (dataSet.name, dataSet.matrix.dumps(), GUID, dataSet.dataType, pickle.dumps(DSUnits.arbitrary()), pickle.dumps(DSPrefix.DSPRefix())))

            for axis in dataSet.axes:
                c.execute("INSERT INTO DataSets (Key, Name, Data, GUID, Type, Units, Prefix, timeStamp) VALUES (NULL, ?, ?, ?, ?, ?, ?,  CURRENT_TIMESTAMP);", (name, data.dumps(), GUID, dataType, pickle.dumps(units), pickle.dumps(prefix)))

            conn.commit()
            conn.close()
            data = {'GUID': GUID, 'Type': 'Data', 'Name': dataSet.name, 'Units': DSUnits.arbitrary().baseQuantity}

class DSWorkspace():
    workspaceURL = ''
    directoryURL = os.path.dirname(os.path.realpath(__file__))
    userProfile = {}
    settingsURL = 'settings.json'
    userScripts = None
    ITEM_GUID = Qt.UserRole
    ITEM_TYPE = Qt.UserRole+1
    ITEM_NAME = Qt.UserRole+2
    ITEM_UNITS = Qt.UserRole+3

    def __init__(self, mainWindow):
        super().__init__()
        self.mainWindow = mainWindow
        self.readSettings()
        self.workspaceTreeWidget = None #Will be loaded in by mainWindow
        self.buildUserScripts()
        self.initDatabaseCommManager()
        self.initInstrumentManager()
        self.initHardwareManager()
        
    def initHardwareManager(self):
        filtersURL = os.path.join(str(Path(self.directoryURL).parent), 'User Filters')
        driversURL = os.path.join(str(Path(self.directoryURL).parent), 'Hardware Drivers')
        self.DSHardwareManager = HardwareManager(self, filtersURL, driversURL)

    def initInstrumentManager(self):
        componentsURL = os.path.join(str(Path(self.directoryURL).parent), 'User Components')
        instrumentsURL = os.path.join(str(Path(self.directoryURL).parent), 'User Instruments')
        self.DSInstrumentManager = InstrumentManager(self, instrumentsURL, componentsURL)

    def initDatabaseCommManager(self):
        self.DBCommMgr = databaseCommManager(self)

    def readSettings(self):
        self.mainWindow.postLog('Loading Settings... ', DSConstants.LOG_PRIORITY_HIGH)
        if(os.path.isfile(self.settingsURL)):
            with open(self.settingsURL, 'r+') as inFile:
                try:
                    self.settings = json.load(inFile)
                    inFile.close()
                    self.mainWindow.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)
                except ValueError:
                    self.mainWindow.postLog('Settings File is Corrupt!!! Making New One..', DSConstants.LOG_PRIORITY_HIGH)
                    inFile.close()
                    self.settings = self.generateDefaultSettingsFile()
                    self.updateSettings()
        else:
            self.mainWindow.postLog('Settings File Not Found! Making New One..', DSConstants.LOG_PRIORITY_HIGH)
            self.settings = self.generateDefaultSettingsFile()
            self.updateSettings()

    def updateSettings(self):
        self.mainWindow.postLog('Updating Settings File... ', DSConstants.LOG_PRIORITY_HIGH)
        with open(self.settingsURL, 'w') as file:
            json.dump(self.settings, file, sort_keys=True, indent=4)
        self.mainWindow.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)

    def generateDefaultSettingsFile(self):
        data = {'Default Importers': {}}
        return data

    def buildUserScripts(self):
        scriptsURL = os.path.join(str(Path(self.directoryURL).parent), 'User Scripts')
        self.userScripts = userScriptsController(scriptsURL, self)

    def setLoadedWorkspace(self, URL):
        self.workspaceURL = URL
        self.directoryURL = os.path.dirname(URL)
        self.settings['workspaceURL'] = URL

        self.mainWindow.workspaceTreeDockWidget.setWindowTitle(os.path.basename(URL))
        self.mainWindow.updateState(DSConstants.MW_STATE_WORKSPACE_LOADED)

    def newWorkspace(self):
        fname = QFileDialog.getSaveFileName(self.mainWindow, 'Save File', self.directoryURL, filter='*.db')
        if fname[0]:
            self.workspaceTreeWidget.clear()
            xmlString = tostring(self.workspaceTreeWidget.toXML(), encoding="unicode")
            self.setLoadedWorkspace(fname[0])
            conn = sqlite3.connect(fname[0])
            c = conn.cursor()
            c.execute('DROP TABLE IF EXISTS Workspace')
            c.execute('CREATE TABLE Workspace (bWorkspace TEXT NOT NULL, timeStamp date);')
            c.execute("INSERT INTO Workspace (bWorkspace, timeStamp) VALUES (?, CURRENT_TIMESTAMP);", (xmlString, )) #memoryview()
            conn.commit()
            conn.close()

    def saveWSToNewSql(self):
        fname = QFileDialog.getSaveFileName(self.mainWindow, 'Save File', self.directoryURL)
        if fname[0]:
            self.setLoadedWorkspace(fname[0])
            self.saveWSToSql()

    def saveWSToSql(self):
        xmlString = tostring(self.workspaceTreeWidget.toXML(), encoding="unicode")
        conn = sqlite3.connect(self.workspaceURL)
        c = conn.cursor()
        c.execute('DROP TABLE IF EXISTS Workspace')
        c.execute('CREATE TABLE Workspace (bWorkspace TEXT NOT NULL, timeStamp date);')
        c.execute("INSERT INTO Workspace (bWorkspace, timeStamp) VALUES (?, CURRENT_TIMESTAMP);", (xmlString, )) #memoryview()
        conn.commit()
        conn.close()

    def saveDSToSql(self, name, data, dataType, units, prefix):
        GUID = str(uuid.uuid4().hex)
        GUID = GUID.upper()
        conn = sqlite3.connect(self.workspaceURL)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS DataSets (Key INTEGER PRIMARY KEY ASC, Name TEXT NOT NULL, Data Blob, Type TEXT, Units Blob, Prefix Blob, GUID TEXT, timeStamp date);')
        c.execute("INSERT INTO DataSets (Key, Name, Data, GUID, Type, Units, Prefix, timeStamp) VALUES (NULL, ?, ?, ?, ?, ?, ?,  CURRENT_TIMESTAMP);", (name, data.dumps(), GUID, dataType, pickle.dumps(units), pickle.dumps(prefix)))
        conn.commit()
        conn.close()
        return GUID

    def submitResultsToWorkspace(self, Op, dataSet):
        axisList = []
        for axis in dataSet.axes:
            axisData = {'GUID': self.saveDSToSql(axis.name, axis.vector, 'Axis', axis.units, axis.prefix), 'Type': 'Axis', 'Name': axis.name, 'Units': axis.units.baseQuantity}
            axisList.append(axisData)

        data = {'GUID': self.saveDSToSql(self.cleanStringName(dataSet.name), dataSet.matrix, 'Matrix', DSUnits.arbitrary(), DSPrefix.DSPRefix()), 'Type': 'Data', 'Name': self.cleanStringName(dataSet.name), 'Units': DSUnits.arbitrary().baseQuantity}
        if(Op is not None):
            parent = self.workspaceTreeWidget.addItem(Op, data)
        else:
            parent = self.workspaceTreeWidget.addItem(self.workspaceTreeWidget.invisibleRootItem(), data)

        for axisDataItem in axisList:
            self.workspaceTreeWidget.addItem(parent, axisDataItem)

        self.saveWSToSql()

    def deleteDSFromSql(self, selectedItem):
        conn = sqlite3.connect(self.workspaceURL)
        c = conn.cursor()
        GUID = selectedItem.data(0, self.ITEM_GUID)
        c.execute('DELETE FROM DataSets WHERE GUID=?', (GUID, ))
        conn.commit()
        conn.close()

        self.saveWSToSql()

    def renameDSInSql(self, selectedItem):
        conn = sqlite3.connect(self.workspaceURL)
        c = conn.cursor()
        GUID = selectedItem.data(0, self.ITEM_GUID)
        c.execute('UPDATE DataSets SET Name = ? WHERE GUID=?', (selectedItem.text(0), GUID, ))
        conn.commit()
        conn.close()

        self.saveWSToSql()

    def loadPreviousWS(self):
        if('workspaceURL' in self.settings):
            if(isinstance(self.settings['workspaceURL'], str) is True):
                if(os.path.isfile(self.settings['workspaceURL']) is True):
                    self.loadWSFromSql(self.settings['workspaceURL'])
            else:
                self.settings['workspaceURL'] = None

    def loadWSFromSql(self, url=None):
        if(url is False):
            dataURL = os.path.join(str(Path(self.directoryURL).parent), 'User Data')
            fname = QFileDialog.getOpenFileName(self.mainWindow, 'Open File', dataURL, filter='*.db')
        else:
            fname = list()
            fname.append(url)

        if fname[0]:
            self.setLoadedWorkspace(fname[0])
            conn = sqlite3.connect(fname[0])
            c = conn.cursor()
            c.execute('SELECT bWorkspace, timeStamp FROM Workspace;')
            results = c.fetchone()
            bWorkspace = results[0]
            timeStamp = results[1]
            self.workspaceTreeWidget.fromXML(bWorkspace)
            conn.commit()
            conn.close()

    def cleanStringName(self, str):
        str = str.replace(" ", "_")
        return str

    def importData(self):
        fname = QFileDialog.getOpenFileNames(self.mainWindow, 'Open File', self.workspaceURL, filter=self.userScripts.genImportDialogFilter())
        for fileURL in fname[0]:
            fileName, fileExtension = os.path.splitext(fileURL)
            self.userScripts.runDefaultImporter(fileURL, fileExtension)

    def importDataByURL(self, fileURL):
        fileName, fileExtension = os.path.splitext(fileURL)
        self.userScripts.runDefaultImporter(fileURL, fileExtension)

    def getScriptIODataFromSQLByGUID(self, GUID):
        conn = sqlite3.connect(self.workspaceURL)
        c = conn.cursor()
        c.execute('SELECT Name, Data, Prefix, Units FROM DataSets WHERE GUID=?', (GUID, ))
        results = c.fetchone()
        conn.commit()
        conn.close()
        if(results):
            DataSet = ScriptIOData(name=results[0])
            DataSet.setMatrix(np.loads(results[1]))
            DataSet.prefix = pickle.loads(results[2])
            DataSet.units = pickle.loads(results[3])

            axesGUIDList = self.workspaceTreeWidget.getAxisGUIDsByDataGUID(GUID)
            for axisGUID in axesGUIDList:
                DataSet.axes.append(self.getScriptIOAxisFromSQLByGUID(axisGUID))
            return DataSet
        else:
            return None

    def getScriptIOAxisFromSQLByGUID(self, GUID):
        conn = sqlite3.connect(self.workspaceURL)
        c = conn.cursor()
        c.execute('SELECT Name, Data, Prefix, Units FROM DataSets WHERE GUID=?', (GUID, ))
        results = c.fetchone()
        conn.commit()
        conn.close()
        if(results):
            Axis = ScriptIOAxis(name=results[0])
            Axis.setVector(np.loads(results[1]))
            Axis.prefix = pickle.loads(results[2])
            Axis.units = pickle.loads(results[3])
            return Axis
        else:
            return None

    def surfacePlotItem(self, selectedItem):
        dockWidget = QDockWidget(selectedItem.text(0), self.mainWindow)
        multiWidget = QWidget()
        layout = QGridLayout()
        pltFigure = plt.figure()
        pltCanvas = FigureCanvas(pltFigure)
        pltToolbar = NavigationToolbar(pltCanvas, dockWidget)
        layout.addWidget(pltToolbar)
        layout.addWidget(pltCanvas)
        multiWidget.setLayout(layout)
        dockWidget.setWidget(multiWidget)
        dockWidget.setAttribute(Qt.WA_DeleteOnClose)
        self.mainWindow.addDockWidget(Qt.RightDockWidgetArea, dockWidget)
        dockWidget.setFloating(True)
        GUID = selectedItem.data(0, self.ITEM_GUID)
        dataSet = self.getScriptIODataFromSQLByGUID(GUID)
        data = dataSet.matrix
        ax = pltFigure.add_subplot(111, projection='3d')

        if isinstance(data, np.ndarray):
            if len(data.shape) == 2:
                row, col = data.shape
                xValues = np.arange(row)
                yValues = np.arange(col)
                x, y = np.meshgrid(xValues, yValues)
                ax.set_zlim(np.min(data), np.max(data))
                ax.set_xlim(np.min(xValues), np.max(xValues))
                ax.set_ylim(np.min(yValues), np.max(yValues))
                ax.view_init(elev=45, azim=45)
                ax.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
                ax.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
                ax.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
                ax.w_xaxis.line.set_color((1.0, 1.0, 1.0, 1.0))
                ax.w_yaxis.line.set_color((1.0, 1.0, 1.0, 1.0))
                ax.w_zaxis.line.set_color((1.0, 1.0, 1.0, 1.0))
                ax.set_xticks([])
                ax.set_yticks([])
                ax.set_zticks([])
                try:
                    ax.plot_surface(x, y, data.T, rstride=1, cstride=1000,
                                    cmap='GnBu', lw=0.1)
                except:
                    pass
            else:
                dockWidget.close()
        else:
            dockWidget.close()

    def linePlotItem(self, selectedItem):
        dockWidget = QDockWidget(selectedItem.text(0), self.mainWindow)
        multiWidget = QWidget()
        layout = QGridLayout()
        pltFigure = plt.figure()
        pltCanvas = FigureCanvas(pltFigure)
        pltToolbar = NavigationToolbar(pltCanvas, dockWidget)
        layout.addWidget(pltToolbar)
        layout.addWidget(pltCanvas)
        multiWidget.setLayout(layout)
        dockWidget.setWidget(multiWidget)
        dockWidget.setAttribute(Qt.WA_DeleteOnClose)
        self.mainWindow.addDockWidget(Qt.RightDockWidgetArea, dockWidget)
        dockWidget.setFloating(True)
        GUID = selectedItem.data(0, self.ITEM_GUID)
        dataSet = self.getScriptIODataFromSQLByGUID(GUID)
        data = dataSet.matrix
        ax = pltFigure.add_subplot(111)
        if isinstance(data, np.ndarray):
            if len(data.shape) == 1:
                ax.plot(data)
            elif len(data.shape) == 2:
                row, col = data.shape
                if col == 1:
                    try:
                        ax.plot(data[:, 0])
                    except:
                        # Should add in a popup for the user to know that
                        # the argument was wrong, or some other feedback.
                        pass
                elif col == 2:
                    try:
                        ax.plot(data[:, 0], data[:, 1])
                    except:
                        pass
                elif row == 2:
                    try:
                        ax.plot(data[0], data[1])
                    except:
                        pass
                else:
                    dockWidget.close()
            else:
                dockWidget.close()
        else:
            dockWidget.close()