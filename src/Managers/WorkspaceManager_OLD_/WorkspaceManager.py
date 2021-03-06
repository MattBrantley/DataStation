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

from src.Managers.WorkspaceManager.UserScriptsController import userScriptsController
from src.Managers.WorkspaceManager.UserScript import *
from src.Managers.InstrumentManager.InstrumentManager import InstrumentManager
from src.Managers.HardwareManager.HardwareManager import HardwareManager
from src.Constants import DSConstants as DSConstants

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

class WorkspaceManager():
    workspaceURL = ''
    userProfile = {}
    settingsURL = 'settings.json'
    userScriptController = None
    ITEM_GUID = Qt.UserRole
    ITEM_TYPE = Qt.UserRole+1
    ITEM_NAME = Qt.UserRole+2
    ITEM_UNITS = Qt.UserRole+3

    def __init__(self, ds):
        super().__init__()
        self.ds = ds
        self.filtersDir = os.path.join(self.ds.rootDir, 'User Filters')
        self.scriptsDir = os.path.join(self.ds.rootDir, 'User Scripts')
        self.userDataDir = os.path.join(self.ds.rootDir, 'User Data')
        self.hardwareDriversDir = os.path.join(self.ds.rootDir, 'Hardware Drivers')
        self.workspaceTreeWidget = None #Will be loaded in by ds

        self.readSettings()

        self.ds.DataStation_Closing_Final.connect(self.updateSettings)

    def connections(self, iM, hM):
        self.iM = iM
        self.hM = hM
        
        self.iM.Instrument_Loaded.connect(self.instrumentLoaded)

    def instrumentLoaded(self):
        self.userProfile['instrumentURL'] = self.iM.currentInstrument.url

    #def connectWidgets(self):
    #    self.userScriptController.connectWidgets()
        
    def initDatabaseCommManager(self):
        self.DBCommMgr = databaseCommManager(self)

    def readSettings(self):
        self.ds.postLog('Loading Settings... ', DSConstants.LOG_PRIORITY_HIGH)
        if(os.path.isfile(self.settingsURL)):
            with open(self.settingsURL, 'r+') as inFile:
                try:
                    self.settings = json.load(inFile)
                    inFile.close()
                    self.ds.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)
                except ValueError:
                    self.ds.postLog('Settings File is Corrupt!!! Making New One..', DSConstants.LOG_PRIORITY_HIGH)
                    inFile.close()
                    self.settings = self.generateDefaultSettingsFile()
                    self.updateSettings()
        else:
            self.ds.postLog('Settings File Not Found! Making New One..', DSConstants.LOG_PRIORITY_HIGH)
            self.settings = self.generateDefaultSettingsFile()
            self.updateSettings()

    def updateSettings(self):
        self.ds.postLog('Updating Settings File... ', DSConstants.LOG_PRIORITY_HIGH)
        with open(self.settingsURL, 'w') as file:
            json.dump(self.settings, file, sort_keys=True, indent=4)
        self.ds.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)

    def generateDefaultSettingsFile(self):
        data = {'Default Importers': {}}
        return data

    def initUserScriptController(self):
        self.userScriptController = userScriptsController(self.scriptsDir, self)

    def setLoadedWorkspace(self, URL):
        self.workspaceURL = URL
        self.settings['workspaceURL'] = URL

        self.ds.workspaceTreeDockWidget.setWindowTitle(os.path.basename(URL))
        self.ds.workspaceTreeDockWidget.updateState(DSConstants.MW_STATE_WORKSPACE_LOADED)

    def newWorkspace(self):
        fname = QFileDialog.getSaveFileName(self.ds, 'Save File', self.userDataDir, filter='*.db')
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
        fname = QFileDialog.getSaveFileName(self.ds, 'Save File', self.userDataDir)
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
            fname = QFileDialog.getOpenFileName(self.ds, 'Open File', self.userDataDir, filter='*.db')
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
        fname = QFileDialog.getOpenFileNames(self.ds, 'Open File', self.workspaceURL, filter=self.userScripts.genImportDialogFilter())
        for fileURL in fname[0]:
            fileName, fileExtension = os.path.splitext(fileURL)
            self.userScriptController.runDefaultImporter(fileURL, fileExtension)

    def importDataByURL(self, fileURL):
        fileName, fileExtension = os.path.splitext(fileURL)
        self.userScriptController.runDefaultImporter(fileURL, fileExtension)

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