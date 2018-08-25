from PyQt5.Qt import *
import os, random
from Constants import DSConstants as DSConstants
from Sockets import *
import numpy as np
from DSWidgets.controlWidget import readyCheckPacket

class Component():
    componentType = 'Default Component'
    componentIdentifier = 'DefComp'
    componentVersion = '1.0'
    componentCreator = 'Matthew R. Brantley'
    componentVersionDate = '7/13/2018'
    iconGraphicSrc = 'default.png' # Not adjustable like layoutGraphicSrc is.
    mainWindow = None
    valid = False

    def __init__(self, instrumentManager, **kwargs):
        self.compSettings = {}
        self.compSettings['name'] = ''
        self.compSettings['layoutGraphicSrc'] = self.iconGraphicSrc
        self.compSettings['showSequencer'] = False
        self.instrumentManager = instrumentManager
        self.name = kwargs.get('name', self.componentType)
        self.socketList = list()
        self.pathDataPackets = list()
        self.pathDataPackets.append(None)
        self.sequencerEditWidget = None
        self.sequencerEventTypes = list()

    def addDCSocket(self, name):
        socket = DCSocket(self, name, 0, 10, 0.1)
        self.socketList.append(socket)

    def registeriViewComponent(self, component):
        self.iViewComponent = component

    def onSequencerDoubleClick(self, eventPos):
        if(self.sequencerEditWidget is None): #Generates this widget the first time it is made.
            self.sequencerEditWidget = sequenceEditWidget(self)

        self.sequencerEditWidget.move(eventPos + QPoint(2, 2))
        if(self.sequencerEditWidget.isHidden()):
            self.sequencerEditWidget.show()
        else:
            self.sequencerEditWidget.hide()

    def redrawSequence(self):
        self.instrumentManager.mainWindow.sequencerDockWidget.updatePlotList()
        self.instrumentManager.mainWindow.hardwareWidget.drawScene()

    def onSaveParent(self):
        savePacket = dict()
        savePacket['compSettings'] = self.compSettings
        savePacket['compType'] = self.componentType
        savePacket['compIdentifier'] = self.componentIdentifier
        savePacket['iViewSettings'] = self.iViewComponent.onSave()
        savePacket['sockets'] = self.saveSockets()

        return savePacket

    def loadCompSettings(self, compSettings):
        self.compSettings = compSettings

    def saveSockets(self):
        sockets = list()
        for socket in self.socketList:
            sockets.append(socket.onSave())
        
        return sockets

    def loadSockets(self, sockets):
        index = 0
        for socket in sockets:
            self.socketList[index].onLoad(socket)

    def getSetting(self, key):
        return self.compSettings[key]

    def setupWidgets(self):
        self.mainWindow = self.instrumentManager.mainWindow
        self.configWidget = ComponentConfigWidget(self)
        self.sequenceEditWidget = ComponentSequenceEditWidget(self)

    def onCreationParent(self):
        self.instrumentManager.mainWindow.postLog('Added New Component to Instrument: ' + self.componentType, DSConstants.LOG_PRIORITY_MED)
        self.onCreation()

    def onCreation(self):
        pass

    def onCreationFinishedParent(self):
        #Walks through all appropriate objects and adds the update call.
        for widget in self.configWidget.findChildren(QLineEdit):
            widget.textChanged.connect(self.redrawSequence)

        for widget in self.configWidget.findChildren(QCheckBox):
            widget.stateChanged.connect(self.redrawSequence)

        for widget in self.configWidget.findChildren(QDoubleSpinBox):
            widget.valueChanged.connect(self.redrawSequence)

    def onRemovalParent(self):
        self.instrumentManager.mainWindow.postLog('Removing Instrument Component: ' + self.componentType, DSConstants.LOG_PRIORITY_MED)
        self.onRemoval()

    def onRemoval(self):
        pass

    def hideConfigWindow(self):
        self.configWidget.hide()

    def onLeftClick(self, eventPos):
        self.configWidget.move(eventPos + QPoint(2, 2))
        if(self.configWidget.isHidden()):
            self.configWidget.show()
        else:
            self.configWidget.hide()

    def ROIRemove(self, eventPos):
        self.instrumentManager.currentInstrument.removeComponent(self)

    def plotSequencer(self):
        return np.array([0,0])

    def readyCheck(self):
        subs = list()
        goodToContinue = True
        for socket in self.socketList:
            newSub = socket.readyCheck()
            subs.append(newSub)
            if(newSub.readyStatus == DSConstants.READY_CHECK_ERROR):
                goodToContinue = False
        
        if(goodToContinue is True):
            runResults = self.onRun()
            if(isinstance(runResults, readyCheckPacket)):
                subs.append(runResults)
                if(runResults.readyStatus == DSConstants.READY_CHECK_ERROR):
                    goodToContinue = False
            else:
                if(runResults is not True):
                    subs.append(readyCheckPacket('User Component', DSConstants.READY_CHECK_ERROR, msg='User Component onRun() Did Not Return readyCheckPacket or True!'))
                    goodToContinue = False
        
        if(goodToContinue is True):
            index = 0
            for socket in self.socketList:
                if(self.pathDataPackets[index] is not None):
                    subs.append(socket.onDataToSourcesParent(self.pathDataPackets[index]))
                else:
                    subs.append(readyCheckPacket('User Component', DSConstants.READY_CHECK_ERROR, msg='User Component onRun() Did Not Populate pathDataPackets for Path #' + str(index+1) + '!'))
                index = index + 1
    
        if(goodToContinue is True):
            return readyCheckPacket('Component', DSConstants.READY_CHECK_READY, subs=subs)
        else:
            return readyCheckPacket('Component', DSConstants.READY_CHECK_ERROR, subs=subs)

    def setPathDataPacket(self, pathNo, packet):
        self.pathDataPackets[pathNo-1] = packet

    def onRun(self):
        return readyCheckPacket('Component', DSConstants.READY_CHECK_ERROR, msg='User Component Does Not Override onRun()!')

    def addSequencerEventType(self, name):
        self.sequencerEventTypes.append(sequencerEventType(name))

class sequenceEditWidget(QDockWidget):
    doNotAutoPopulate = True

    def __init__(self, compParent):
        super().__init__('Sequencer: ' + compParent.name, parent=compParent.mainWindow.sequencerDockWidget)
        self.compParent = compParent
        self.setFeatures(QDockWidget.DockWidgetClosable)
        self.setMinimumSize(QSize(350,450))
        self.setFloating(True)
        self.hide()
        self.mainWidget = QWidget()
        self.layout = QVBoxLayout()
        self.mainWidget.setLayout(self.layout)
        self.sequencerEventTypes = compParent.sequencerEventTypes

        self.layout.addWidget(self.initTableWidget())
        self.layout.addWidget(self.initButtonsWidget())

        self.setWidget(self.mainWidget)

    def initTableWidget(self):
        self.table = QTableWidget(0,3)
        self.table.setHorizontalHeaderLabels(['Time (s)', 'Type', 'Settings'])
        #self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        #self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.itemSelectionChanged.connect(self.tableSelectionChanged)

        return self.table

    def initButtonsWidget(self):
        self.buttonWidget = QWidget()
        self.buttonWidgetLayout = QHBoxLayout()
        self.buttonWidget.setLayout(self.buttonWidgetLayout)

        self.addButton = QPushButton('New')
        self.addButton.pressed.connect(self.newButtonPressed)
        self.editButton = QPushButton('Edit')
        self.editButton.setEnabled(False)
        self.editButton.pressed.connect(self.editButtonPressed)
        self.removeButton = QPushButton('Remove')
        self.removeButton.setEnabled(False)
        self.removeButton.pressed.connect(self.removeButtonPressed)

        self.buttonWidgetLayout.addWidget(self.addButton)
        self.buttonWidgetLayout.addWidget(self.editButton)
        self.buttonWidgetLayout.addWidget(self.removeButton)

        return self.buttonWidget

    def newButtonPressed(self):
        menu = QMenu()

        newConfig = QWidget()
        newConfigAction = QWidgetAction(newConfig)
        newConfigAction.setDefaultWidget(newConfig)
        mainLayout = QVBoxLayout()
        buttonWidget = QWidget()
        buttonLayout = QFormLayout()
        buttonWidget.setLayout(buttonLayout)
        newConfig.setLayout(mainLayout)
        acceptButton = QPushButton("Accept")
        mainLayout.addWidget(buttonWidget)
        mainLayout.addWidget(acceptButton)
        menu.addAction(newConfigAction)

        timeBox = QDoubleSpinBox()
        buttonLayout.addRow('Time (s)', timeBox)
        actionBox = QComboBox()
        actionBox.addItem('Step')
        buttonLayout.addRow('Action', actionBox)
        voltageBox = QDoubleSpinBox()
        buttonLayout.addRow('Voltage (v)', voltageBox)

        #action = menu.exec_(QCursor().pos())


        rowCount = self.table.rowCount()
        self.table.insertRow(rowCount)
        self.table.setCellWidget(rowCount, 1, self.genTypeWidget())
        #self.table.setItem(rowCount, 1, QTableWidgetItem('Hi' + str(rowCount)))

    def genTypeWidget(self):
        selector = eventTypeComboBox(self.sequencerEventTypes)
        return selector

    def editButtonPressed(self):
        pass

    def removeButtonPressed(self):
        rows = self.getTableSelectedRows()
        for row in rows:
            self.table.removeRow(row)

    def getTableSelectedRows(self):
        indexes = self.table.selectedIndexes()
        rowList = list()
        for index in indexes:
            rowList.append(index.row())

        return rowList

    def tableSelectionChanged(self):
        if(len(self.getTableSelectedRows()) > 0):
            self.editButton.setEnabled(True)
            self.removeButton.setEnabled(True)
        else:
            self.editButton.setEnabled(False)
            self.removeButton.setEnabled(False)

class eventTypeComboBox(QComboBox):
    def __init__(self, eventTypes):
        super().__init__()
        #self.addItem('')
        self.eventTypes = eventTypes
        for eventType in self.eventTypes:
            self.addItem(eventType.name)

class sequencerEventType():
    def __init__(self, name):
        self.name = name

class ComponentConfigWidget(QDockWidget):
    doNotAutoPopulate = True

    def __init__(self, compParent):
        super().__init__('Config: ' + compParent.name, parent=compParent.instrumentManager.instrumentWidget)
        self.compParent = compParent
        self.setFeatures(QDockWidget.DockWidgetClosable)
        self.setFloating(True)
        self.hide()

class ComponentSequenceEditWidget(QWidget):
    doNotAutoPopulate = True

    def __init__(self, component):
        super().__init__()
        self.component = component