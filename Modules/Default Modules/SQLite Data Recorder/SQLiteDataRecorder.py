from PyQt5.Qt import *
import time, os
from src.Managers.ModuleManager.DSModule import DSModule
from src.Constants import moduleFlags as mfs
from src.Constants import logObject
from PyQt5.QtSql import *

class SQLiteDataRecorder(DSModule):
    Module_Name = 'SQLite Data Recorder'
    Module_Flags = [mfs.CAN_DELETE]

    def __init__(self, ds, handler):
        super().__init__(ds, handler)
        self.ds = ds
        self.iM = ds.iM
        self.handler = handler
        self.SQLComm = SQLiteDataRecorder_SQLComm(self)
        self.initLayout()

        self.iM.Instrument_Sequence_Running.connect(self.instrumentSequenceRunning)

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
        print('running')
        print(instrument)
        print(instrument.runID)
        
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
        self.dbLabel = QLabel('SQLite Database:')

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
        self.spanBottom.setText('SOMETHING HERE')

        self.layout.addWidget(self.spanBottom)

    def newButtonPressed(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self,"Create New SQLite Database","","SQLite Database (*.sqlite)", options=options)
        if fileName:
            self.module.SQLComm.New_Database(fileName + '.sqlite')
            self.module.bottomWidget.treeWidget.populateIndexes()
            self.spanBottom.setText(fileName + '.sqlite')

    def openButtonPressed(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"Select Existing SQLite Database", "","SQLite Database (*.sqlite)", options=options)
        if fileName:
            self.module.SQLComm.Set_Current_Database(fileName)
            self.module.bottomWidget.treeWidget.populateIndexes()
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

        self.populateIndexes()

    def populateIndexes(self):
        for instrumentRunID in self.module.SQLComm.Get_Instrument_Runs():
            self.addIndex(instrumentRunID)

    def addIndex(self, instrumentRunID):
        indexItem = QTreeWidgetItem([title])
        self.addTopLevelItem(indexItem)

        for measurementPacket in self.module.SQLComm.Get_Measurement_Packets(instrumentRunID):
            measurementItem = QTreeWidgetItem(['ITEM'])
            indexItem.addChild(measurementItem)

class SQLiteDataRecorder_SQLComm():
    def __init__(self, module):
        self.module = module
        self.databaseURL = None
        self.db = None

    def Set_Current_Database(self, url):
        if self.db is not None:
            self.db.close()

        self.databaseURL = url
        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName(url)
        self.Create_Tables()

    def New_Database(self, url):
        new_db = QSqlDatabase.addDatabase('QSQLITE')
        new_db.setDatabaseName(url)

        if not new_db.open():
            new_db.close()
            self.module.ds.postLog('Error Creating SQLite Database At: ' + url)
        else:
            new_db.close()
            self.Set_Current_Database(url)

    def Create_Tables(self):
        if self.db.open():
            print('query')
            query = QSqlQuery()
            query.exec_("CREATE TABLE IF NOT EXISTS instrumentRuns(id int primary key, run_ID varchar(36), instrument_name varchar(100)")

    def Get_Measurement_Packets(self, instrumentRunID):
        if self.databaseURL is not None:
            return list()
        else:
            return list()

    def Get_Instrument_Runs(self):
        if self.databaseURL is not None:
            return list()
        else:
            return list()