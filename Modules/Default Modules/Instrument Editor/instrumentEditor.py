from PyQt5.Qt import *
from PyQt5.QtCore import *
import os, random, numpy as np
from src.Constants import DSConstants as DSConstants, moduleFlags as mfs
from PyQt5.QtGui import *
from src.Managers.ModuleManager.DSModule import DSModule
from componentsList import componentsList
from instrumentView import instrumentView
from loadedInstruments import loadedInstruments
from treeView import treeView

class instrumentEditor(DSModule):
    Module_Name = 'Instrument Editor'
    Module_Flags = [mfs.CAN_DELETE]

    def __init__(self, ds, handler):
        super().__init__(ds, handler)
        self.ds = ds
        self.iM = ds.iM
        self.rootPath = os.path.join(self.ds.rootDir, 'Instruments')
        self.targetUUID = None
        self.targetPath = None
        self.targetInstrument = None

        self.mainContainer = QMainWindow()
        
        self.instrumentNavigator = treeView(self)
        self.componentList = componentsList(self)
        self.loadedInstruments = loadedInstruments(self)
        self.instrumentView = instrumentView(self)

        self.toolWidgets = QTabWidget()
        self.toolWidgets.addTab(self.instrumentNavigator, "Instruments")
        self.toolWidgets.addTab(self.componentList, "Component Pallet")
        self.toolWidgets.addTab(self.loadedInstruments, "Loaded Instruments")

        self.instrumentContainer = QSplitter()
        self.instrumentContainer.addWidget(self.toolWidgets)
        self.instrumentContainer.addWidget(self.instrumentView)

        #self.instrumentContainer.setStretchFactor(1, 3)
        self.setWidget(self.mainContainer) 
        self.mainContainer.setCentralWidget(self.instrumentContainer)

        self.toolbar = QToolBar()
        self.initActions()
        self.initToolbar()
        self.mainContainer.addToolBar(self.toolbar)
        self.updateToolbarState()

        self.iM.Instrument_Removed.connect(self.populateInstrumentList)
        self.iM.Instrument_New.connect(self.newInstrument)
        self.iM.Instrument_Name_Changed.connect(self.newInstrument)
        self.iM.Instrument_New.connect(self.populateInstrumentList)
        self.iM.Instrument_Name_Changed.connect(self.populateInstrumentList)

        prevInstrumentPath = self.Read_Setting('Instrument_Path')
        if isinstance(prevInstrumentPath, str):
            self.openInstrument(prevInstrumentPath)

    def initActions(self):
        self.newAction = QAction('New', self)
        self.newAction.setShortcut('Ctrl+N')
        self.newAction.setStatusTip('New')
        self.newAction.triggered.connect(self.new)

        self.saveAction = QAction('Save', self)
        self.saveAction.setStatusTip('Save')
        self.saveAction.triggered.connect(self.save)

        self.saveAsAction = QAction('Save As', self)
        self.saveAsAction.setStatusTip('Save As')
        self.saveAsAction.triggered.connect(self.saveAs)

        self.toolToggle = QToolButton(self)
        self.toolToggle.setIcon(QIcon(os.path.join(self.ds.srcDir, 'icons3\cogwheels.png')))
        self.toolToggle.setCheckable(True)
        self.toolToggle.setStatusTip('Show/Hide Tools')
        self.toolToggle.toggled.connect(self.toolsToggled)
        self.toolToggle.toggle()

        self.lockToggle = QToolButton(self)
        self.lockToggle.setIcon(QIcon(os.path.join(self.ds.srcDir, 'icons2\padlock.png')))
        self.lockToggle.setCheckable(True)
        self.lockToggle.setStatusTip('Show/Hide Tools')
        self.lockToggle.toggled.connect(self.lockToggled)
        self.lockToggle.toggle()

        self.instrumentSelectionBox = QComboBox(self.toolbar)
        self.instrumentSelectionBox.setMinimumWidth(200)
        self.instrumentSelectionBox.currentIndexChanged.connect(self.instrumentSelectionChanged)

    def populateInstrumentList(self, instrument):
        self.instrumentSelectionBox.clear()
        self.loadedInstruments.clear()
        self.instrumentSelectionBox.addItem('')
        for idx, instrument in enumerate(self.iM.Get_Instruments()):
            self.instrumentSelectionBox.addItem(instrument.Get_Name())
            self.instrumentSelectionBox.setItemData(idx+1, instrument.Get_UUID(), role=Qt.UserRole)
            if(instrument.Get_UUID() == self.targetUUID):
                self.instrumentSelectionBox.setCurrentIndex(idx+1)

            self.loadedInstruments.addInstrument(instrument)

    def newInstrument(self, instrument):
        if os.path.abspath(instrument.Get_Path()) == os.path.abspath(self.targetPath):
            self.targetUUID = instrument.Get_UUID()

    def initToolbar(self):
        self.toolbar.addAction(self.newAction)
        self.toolbar.addAction(self.saveAction)
        self.toolbar.addAction(self.saveAsAction)
        
        self.toolbar.addSeparator()

        self.toolbar.addWidget(self.toolToggle)
        self.toolbar.addWidget(self.lockToggle)

        self.toolbar.addSeparator()

        self.toolbar.addWidget(self.instrumentSelectionBox)
    
    def instrumentSelectionChanged(self, index):
        uuid = self.instrumentSelectionBox.itemData(index, role=Qt.UserRole)
        instrument = self.iM.Get_Instruments(uuid=uuid)

        if not instrument:
            instrument = None
        else:
            instrument = instrument[0]

        self.targetInstrument = instrument

        if(instrument is not None):
            self.setWindowTitle('Instrument View (' + instrument.Get_Name() + ')')
            self.Write_Setting('Instrument_Path', instrument.Get_Path())
        else:
            self.setWindowTitle('Instrument View (None)')
            self.Write_Setting('Instrument_Path', None)

        self.instrumentView.loadTargetInstrument()

    def openInstrument(self, filePath):
        self.targetPath = filePath
        self.iM.Load_Instrument(filePath)

    def new(self):
        self.ds.postLog('Creating new instrument', DSConstants.LOG_PRIORITY_HIGH)
        fname, ok = QInputDialog.getText(self.ds, "Virtual Instrument Name", "Virtual Instrument Name")
        if(ok):
            self.iM.New_Instrument(name=fname, path=self.rootPath)
        else:
            return
        self.updateTitle()

    def save(self):
        savePath = None
        item = self.instrumentNavigator.selectionModel().selectedIndexes()
        if(len(item) > 0):
            savePath = self.instrumentNavigator.model().filePath(item[0])
        else:
            savePath = self.rootPath

        self.targetInstrument.Save_Instrument(path=savePath)

        #if(self.iM.Get_Instrument().Get_Path is None):
        #    self.saveAsInstrument(savePath)
        #else:
        #    self.saveInstrument(savePath)

    def saveAs(self):
        savePath = None
        item = self.instrumentNavigator.selectionModel().selectedIndexes()
        if(len(item) > 0):
            savePath = self.instrumentNavigator.model.filePath(item[0])
        else:
            savePath = self.rootPath
        self.saveAsInstrument(savePath)

    def saveAsInstrument(self, savePath):
        fname, ok = QInputDialog.getText(self.ds, "Virtual Instrument Name", "Virtual Instrument Name")
        checkPath = os.path.join(savePath, fname + '.dsinstrument')
        if(ok):
            pass
        else:
            return

        if(os.path.exists(checkPath)):
            reply = QMessageBox.question(self.ds, 'File Warning!', 'File exists - overwrite?', QMessageBox.Yes, QMessageBox.No)
            if(reply == QMessageBox.No):
                return

        self.iM.Save_Instrument(name=fname, path=savePath)

    def saveInstrument(self, savePath):
        if(self.targetInstrument.Get_Name() == 'Default Instrument'):
            fname, ok = QInputDialog.getText(self.ds, "Virtual Instrument Name", "Virtual Instrument Name")
            if(ok):
                self.iM.Get_Instruemnt().Set_Name(fname)
            else:
                return

        self.iM.Save_Instrument()

    def toolsToggled(self, checked):
        if(checked):
            self.toolWidgets.show()
        else:
            self.toolWidgets.hide()

    def lockToggled(self, checked):
        if(checked):
            pass
            #self.instrumentView.setDragEnabled(False)
            #self.instrumentView.setAcceptDrops(False)
        else:
            pass
            #self.instrumentView.setDragEnabled(True)
            #self.instrumentView.setAcceptDrops(True)

    def doubleClicked(self, index):
        item = self.fileSystem.fileInfo(index)
        filePath = item.filePath()
        fileExt = os.path.splitext(item.fileName())[1]
        if(fileExt == '.sqpy'):
            self.openInstrument(filePath)

    def updateToolbarState(self):
        self.saveAction.setEnabled(True)
        self.saveAsAction.setEnabled(True)