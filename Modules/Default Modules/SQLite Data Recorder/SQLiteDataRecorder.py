from PyQt5.Qt import *
from PyQt5.QtCore import QThread
import time, os, sqlite3
from src.Constants import DSConstants as DSConstants
from src.Managers.ModuleManager.DSModule import DSModule
from src.Constants import moduleFlags as mfs
from src.Constants import logObject
import pickle


class SQLiteDataRecorder(DSModule):
    Module_Name = 'SQLite Data Recorder'
    Module_Flags = [mfs.CAN_DELETE]

    Instrument_Sequence_Running = pyqtSignal(object) # instrument
    Socket_Measurement_Packet_Recieved = pyqtSignal(object, object, object, object) # instrument, component, socket, measurementPacket
    Open_Connections = pyqtSignal()
    Populate_Preview = pyqtSignal()

    def __init__(self, ds, handler):
        super().__init__(ds, handler)
        self.ds = ds
        self.iM = ds.iM
        self.handler = handler
        self.SQLComm = None
        self.commStarted = False
        self.initLayout()
        self.iM.Instrument_Sequence_Running.connect(self.instrumentSequenceRunning)
        self.iM.Socket_Measurement_Packet_Recieved.connect(self.socketMeasurementPacketRecieved)
        self.commThread = None

    def connectDatabase(self, url):
        if self.commThread is not None:
            self.commThread.exit()
        self.SQLComm = SQLiteDataRecorder_SQLComm(self, url)
        self.commThread = QThread()

        self.SQLComm.Comm_Opened.connect(self.commOpened)
        self.SQLComm.Error_Message.connect(self.commErrorMessage)
        self.SQLComm.Comm_Writing.connect(self.commWriting)
        self.SQLComm.Comm_Reading.connect(self.commReading)
        self.SQLComm.Found_Instrument_Run.connect(self.foundInstrumentRun)

        self.SQLComm.moveToThread(self.commThread)

        self.Instrument_Sequence_Running.connect(self.SQLComm.Record_Instrument_Run)
        self.Socket_Measurement_Packet_Recieved.connect(self.SQLComm.Record_Measurement_Packet)
        self.Open_Connections.connect(self.SQLComm.Open_Connections)
        self.Populate_Preview.connect(self.SQLComm.Get_Instrument_Runs)

        self.commThread.start()
        self.Open_Connections.emit()

    def foundInstrumentRun(self, runObject):
        self.bottomWidget.treeWidget.addIndex(runObject)

    def commOpened(self, toggle):
        self.commStarted = toggle
        if toggle is True:
            self.bottomWidget.treeWidget.populateIndexes()

    def commWriting(self, toggle):
        if toggle is True:
            self.topWidget.dbLabel.setText('SQLite Database: Writing..')
        else:
            self.topWidget.dbLabel.setText('SQLite Database: Idle..')

    def commReading(self, toggle):
        if toggle is True:
            self.topWidget.dbLabel.setText('SQLite Database: Reading..')
        else:
            self.topWidget.dbLabel.setText('SQLite Database: Idle..')

    def commErrorMessage(self, string, errorObject):
        self.ds.postLog(string, DSConstants.LOG_PRIORITY_HIGH)
        self.ds.postLog('    ->' + repr(errorObject), DSConstants.LOG_PRIORITY_HIGH)

    def initLayout(self):
        self.mainWidget = QWidget()
        self.mainLayout = QVBoxLayout()
        self.mainWidget.setLayout(self.mainLayout)
        self.topWidget = SQLiteDataRecorder_Top(self)
        self.bottomWidget = SQLiteDataRecorder_Bottom(self)
        self.mainLayout.addWidget(self.topWidget)
        self.mainLayout.addWidget(self.bottomWidget)

        self.setWidget(self.mainWidget)

    def instrumentSequenceRunning(self, instrument):
        self.Instrument_Sequence_Running.emit(instrument)
        
    def socketMeasurementPacketRecieved(self, instrument, component, socket, measurementPacket):
        self.Socket_Measurement_Packet_Recieved.emit(instrument, component, socket, measurementPacket)

class SQLiteDataRecorder_Top(QWidget):
    def __init__(self, module):
        super().__init__()
        self.module = module
        self.initTop()

    def initTop(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        ##### First Row #####
        self.spanTop = QWidget()
        self.spanTopLayout = QHBoxLayout()
        self.spanTop.setLayout(self.spanTopLayout)
        self.dbLabel = QLabel('SQLite Database: Idle..')

        self.newIcon = QIcon(QPixmap(os.path.join(self.module.ds.srcDir, 'icons6/002-add.png')))
        self.newButton = QPushButton()
        self.newButton.setIcon(self.newIcon)
        self.newButton.setFixedSize(40, 40)
        self.newButton.pressed.connect(self.newButtonPressed)

        self.openIcon = QIcon(QPixmap(os.path.join(self.module.ds.srcDir, 'icons6/004-file-1.png')))
        self.openButton = QPushButton()
        self.openButton.setIcon(self.openIcon)
        self.openButton.setFixedSize(40, 40)
        self.openButton.pressed.connect(self.openButtonPressed)

        self.refreshIcon = QIcon(QPixmap(os.path.join(self.module.ds.srcDir, 'icons5/refresh.png')))
        self.refreshButton = QPushButton()
        self.refreshButton.setIcon(self.refreshIcon)
        self.refreshButton.setFixedSize(40, 40)
        self.refreshButton.pressed.connect(self.refreshButtonPressed)

        self.spanTopLayout.addWidget(self.dbLabel)
        self.spanTopLayout.addWidget(self.newButton)
        self.spanTopLayout.addWidget(self.openButton)
        self.spanTopLayout.addWidget(self.refreshButton)

        self.layout.addWidget(self.spanTop)

        ##### Second Row #####
        self.spanBottom = QLineEdit()
        self.spanBottom.setEnabled(False)
        self.spanBottom.setText('No SQLite File Selected!')

        self.layout.addWidget(self.spanBottom)

    def newButtonPressed(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self,"Create New SQLite Database","","SQLite Database (*.sqlite)", options=options)
        if fileName:
            self.module.connectDatabase(fileName + '.sqlite')
            self.module.bottomWidget.treeWidget.populateIndexes()
            self.spanBottom.setText(fileName + '.sqlite')

    def openButtonPressed(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"Select Existing SQLite Database", "","SQLite Database (*.sqlite)", options=options)
        if fileName:
            self.module.connectDatabase(fileName)
            self.spanBottom.setText(fileName)

    def refreshButtonPressed(self):
        self.module.bottomWidget.treeWidget.populateIndexes()

class SQLiteDataRecorder_Bottom(QWidget):
    def __init__(self, module):
        super().__init__()
        self.module = module
        self.initBottom()

    def initBottom(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.treeWidget = SQLiteDataRecorder_TreeWidget(self.module)
        self.layout.addWidget(self.treeWidget)

class SQLiteDataRecorder_TreeWidget(QTreeWidget):
    def __init__(self, module):
        super().__init__()
        self.module = module
        self.setHeaderLabels(['Name', 'Instrument', 'Timestamp', 'Sequence', 'User'])
        self.setColumnCount(5)

    def populateIndexes(self):
        self.module.Populate_Preview.emit()

    def addIndex(self, runObject):
        indexItem = QTreeWidgetItem(['', runObject.instrumentName, runObject.timeStamp])
        self.addTopLevelItem(indexItem)
        for measurement in runObject.measurementList:
            childItem = QTreeWidgetItem(['Measurement: ' + str(measurement['rowID'])])
            indexItem.addChild(childItem)

class SQLiteDataRecorder_SQLComm(QObject):
    Comm_Opened = pyqtSignal(bool)
    Error_Message = pyqtSignal(str, object)
    Comm_Writing = pyqtSignal(bool)
    Comm_Reading = pyqtSignal(bool)
    Found_Instrument_Run = pyqtSignal(object) # Database_Run_Object

    def __init__(self, module, databaseURL):
        super().__init__()
        self.module = module
        self.databaseURL = databaseURL

    def Open_Connections(self):
        self.conn = sqlite3.connect(self.databaseURL)
        self.cursor = self.conn.cursor()

        self.Init_Tables()
        self.Comm_Opened.emit(True)

    def Init_Tables(self):
        with self.conn:
            try:
                self.cursor.execute("CREATE TABLE IF NOT EXISTS instrumentRuns(run_ID varchar(36), instrument_name varchar(100), timestamp varchar(100))")
                self.cursor.execute("CREATE TABLE IF NOT EXISTS measurementPackets(run_ID varchar(36), measurement_packet BLOB)")
            except Exception as e:
                self.Error_Message.emit('ERROR Configuring Tables: ' + self.databaseURL, e)

    def Record_Instrument_Run(self, instrument):
        self.Comm_Writing.emit(True)
        timeStamp = time.strftime('%m/%d/%Y %H:%M:%S', time.localtime())
        with self.conn:
            try:
                self.cursor.execute('INSERT INTO instrumentRuns (run_id, instrument_name, timestamp) VALUES (?, ?, ?)', (instrument.Get_Run_ID(), instrument.Get_Name(), timeStamp))
            except Exception as e:
                self.Error_Message.emit('ERROR Writing Instrument Run To: ' + self.databaseURL, e)
        self.Comm_Writing.emit(False)

    def Record_Measurement_Packet(self, instrument, component, socket, measurementPacket):
        self.Comm_Writing.emit(True)
        with self.conn:
            try:
                packetData = pickle.dumps(measurementPacket, pickle.HIGHEST_PROTOCOL)
                self.cursor.execute('INSERT INTO measurementPackets VALUES (?, ?)', (instrument.Get_Run_ID(), sqlite3.Binary(packetData)))
            except Exception as e:
                self.Error_Message.emit('ERROR Writing Measurement Packet To: ' + self.databaseURL, e)
        self.Comm_Writing.emit(False)

    def Get_Measurement_Packets(self, rowID):
        self.Comm_Reading.emit(True)
        with self.conn:
            try:
                for result in self.cursor.execute('SELECT run_id, instrument_name, timestamp FROM measurementPackets WHERE rowid=?', rowID):
                    pass
            except Exception as e:
                self.Error_Message.emit('ERROR Reading Measurement Packet From: ' + self.databaseURL, e)

        self.Comm_Reading.emit(False)
        return result

    def Get_Instrument_Runs(self):
        self.Comm_Reading.emit(True)
        rowCursor = self.conn.cursor()
        with self.conn:
            try:
                for row in self.cursor.execute('SELECT run_ID, instrument_name, timestamp FROM instrumentRuns'):
                    record = Database_Run_Record(row[0], row[1], row[2])
                    for row2 in rowCursor.execute('SELECT rowid, run_id FROM measurementPackets where run_ID=?', (row[0],)):
                        record.Add_Measurement(row2[0])
                    
                    self.Found_Instrument_Run.emit(record)
            except Exception as e:
                self.Error_Message.emit('ERROR Reading Instrument Run From: ' + self.databaseURL, e)

        self.Comm_Reading.emit(False)

class Database_Run_Record():
    def __init__(self, runID, instrumentName, timeStamp):
        self.runID = runID
        self.instrumentName = instrumentName
        self.timeStamp = timeStamp

        self.measurementList = list()

    def Add_Measurement(self, rowID):
        measurement = dict()
        measurement['rowID'] = rowID

        self.measurementList.append(measurement)
