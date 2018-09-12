from PyQt5.Qt import *
from PyQt5.QtGui import QStandardItemModel
import os, random, uuid
from Constants import DSConstants as DSConstants
from Managers.InstrumentManager.Sockets import *
import numpy as np
from decimal import Decimal
from DSWidgets.controlWidget import readyCheckPacket

class Component(QObject):
    #Component_Modified = pyqtSignal(object)

    #Events_Modified = pyqtSignal(object)

    #Socket_Attached = pyqtSignal(object)
    #Socket_Unattached = pyqtSignal(object)

    indexMe = True
    componentType = 'Default Component'
    componentIdentifier = 'DefComp'
    componentVersion = '1.0'
    componentCreator = 'Matthew R. Brantley'
    componentVersionDate = '7/13/2018'
    iconGraphicSrc = 'default.png' # Not adjustable like layoutGraphicSrc is.
    mW = None
    valid = False
    isTriggerComponent = False

    def __init__(self, mW, **kwargs):
        super().__init__()
        self.allowOverlappingEvents = False
        self.compSettings = {}
        self.compSettings['name'] = ''
        self.compSettings['layoutGraphicSrc'] = self.iconGraphicSrc
        self.compSettings['showSequencer'] = False
        self.compSettings['uuid'] = str(uuid.uuid4())
        self.compSettings['triggerComp'] = False
        self.instr = None           #Factory does not write this. IT's in the very next line in Instrument thought.
        self.mW = mW                #Factory does not write this. It's in the very next line in Instrument though.
        self.iM = None
        self.name = kwargs.get('name', self.componentType)
        self.socketList = list()
        self.pathDataPackets = list()
        self.pathDataPackets.append(None)
        self.sequencerEditWidget = None
        self.sequencerEventTypes = list()
        self.data = None
        self.plotItem = None
        self.sequencerDrawState = False

##### Datastation Interface Functions #####

    def readyCheck(self):
        subs = list()
        goodToContinue = True
        for socket in self.socketList:
            newSub = socket.readyCheck()
            subs.append(newSub)
            if(newSub.readyStatus == DSConstants.READY_CHECK_ERROR):
                goodToContinue = False
        
        if(goodToContinue is True):
            if(self.sequencerEditWidget is not None):
                runResults = self.onRun(self.sequencerEditWidget.getEvents())
            else:
                return readyCheckPacket('User Component [' + self.compSettings['name'] + ']', DSConstants.READY_CHECK_ERROR, subs=subs, msg='User Component Does Not Have SequencerEditWidget!!')
            if(isinstance(runResults, readyCheckPacket)):
                subs.append(runResults)
                if(runResults.readyStatus == DSConstants.READY_CHECK_ERROR):
                    goodToContinue = False
            else:
                if(runResults is not True):
                    subs.append(readyCheckPacket('User Component [' + self.compSettings['name'] + ']', DSConstants.READY_CHECK_ERROR, msg='User Component onRun() Did Not Return readyCheckPacket or True!'))
                    goodToContinue = False
        
        if(goodToContinue is True):
            index = 0
            for socket in self.socketList:
                if(self.pathDataPackets[index] is not None):
                    #if(self.pathDataPackets[index].waveformData is None):
                    #    subs.append(readyCheckPacket('User Component', DSConstants.READY_CHECK_ERROR, msg='User Component onRun() populated and empty packet (no waveformData!)' + str(index+1) + '!'))
                    #else:
                    subs.append(socket.onDataToSourcesParent(self.pathDataPackets[index]))
                else:
                    subs.append(readyCheckPacket('User Component [' + self.compSettings['name'] + ']', DSConstants.READY_CHECK_ERROR, msg='User Component onRun() Did Not Populate pathDataPackets for Path #' + str(index+1) + '!'))
                index = index + 1
    
        if(goodToContinue is True):
            return readyCheckPacket('Component', DSConstants.READY_CHECK_READY, subs=subs)
        else:
            return readyCheckPacket('Component', DSConstants.READY_CHECK_ERROR, subs=subs)

##### Functions Called By Factoried Sockets #####

    def socketAttached(self, socket):
        self.instr.socketAttached(socket, self)

    def socketDetatched(self, socket):
        self.instr.socketDetatched(socket, self)

    def program

##### Functions Over-Ridden By Factoried Components #####

    def onCreationParent(self):
        self.mW.postLog('Added New Component to Instrument: ' + self.componentType, DSConstants.LOG_PRIORITY_MED)
        self.sequencerEditWidget = sequenceEditWidget(self.mW, self)
        self.onCreation()

    def onCreation(self): ### OVERRIDE ME!! ####
        pass

    def onCreationFinishedParent(self):
        #Walks through all appropriate objects and adds the update call.
        for widget in self.configWidget.findChildren(QLineEdit):
            widget.textChanged.connect(self.updatePlot)

        for widget in self.configWidget.findChildren(QCheckBox):
            widget.stateChanged.connect(self.updatePlot)

        for widget in self.configWidget.findChildren(QDoubleSpinBox):
            widget.valueChanged.connect(self.updatePlot)

        self.onCreationFinished()

    def onCreationFinished(self): ### OVERRIDE ME!! ####
        pass

    def onRemovalParent(self):
        self.mW.postLog('Removing Instrument Component: ' + self.componentType, DSConstants.LOG_PRIORITY_MED)
        for socket in self.socketList:
            socket.detatchInputSelf()
        self.onRemoval()

    def onRemoval(self):  ### OVERRIDE ME!! ####
        pass

    def parentPlotSequencer(self):
        if(self.sequencerEditWidget is not None):
            return self.plotSequencer(self.sequencerEditWidget.getEvents())

    def plotSequencer(self, events): ### OVERRIDE ME!! ####
        return np.array([0,0])

    def onRunParent(self, events):
        self.onRun(events)

    def onRun(self, events):  ### OVERRIDE ME!! ####
        return readyCheckPacket('Component', DSConstants.READY_CHECK_ERROR, msg='User Component Does Not Override onRun()!')

##### Component Modifications ######

    def onSaveParent(self):
        savePacket = dict()
        savePacket['compSettings'] = self.compSettings
        savePacket['compType'] = self.componentType
        savePacket['compIdentifier'] = self.componentIdentifier
        savePacket['triggerComp'] = self.isTriggerComponent
        if(hasattr(self, 'iViewComponent')):
            savePacket['iViewSettings'] = self.iViewComponent.onSave()
        savePacket['sockets'] = self.saveSockets()

        return savePacket

    def loadCompSettings(self, compSettings):
        for key, value in compSettings.items():
            self.compSettings[key] = value

    def setPathDataPacket(self, pathNo, packet):
        self.pathDataPackets[pathNo-1] = packet

    def setupWidgets(self):
        self.configWidget = ComponentConfigWidget(self)
        self.sequenceEditWidget = ComponentSequenceEditWidget(self)

##### Event Modifications #####

    def addSequencerEventType(self, sequencerEventType):
        self.sequencerEventTypes.append(sequencerEventType)

    def clearEvents(self):
        if(self.sequencerEditWidget is not None):
            self.sequencerEditWidget.clearEvents()

##### Sequencer Interactions #####

    def registerPlotItem(self, plotItem):
        self.plotItem = plotItem

    def updatePlot(self):
        if(self.compSettings['showSequencer'] is not self.sequencerDrawState):
            self.sequencerDrawState = self.compSettings['showSequencer']
            self.redrawSequence()

        if(self.plotItem is not None):
            self.plotItem.updatePlot()

    def redrawSequence(self):
        self.mW.sequencerDockWidget.updatePlotList()
        self.mW.hardwareWidget.drawScene()

##### Socket Interactions #####

    def reprogramSourceTargets(self):
        for socket in self.socketList:
            source = socket.getAttachedSource()
            if(source is not None):
                source.reprogram()

    def addAOSocket(self, name):
        socket = AOSocket(self, name, 0, 10, 0.1)
        self.socketList.append(socket)
        return socket

    def addAISocket(self, name):
        socket = AISocket(self, name, 0, 10, 0.1)
        self.socketList.append(socket)
        return socket

    def addDOSocket(self, name):
        socket = DOSocket(self, name)
        self.socketList.append(socket)
        return socket

    def addDISocket(self, name):
        socket = DISocket(self, name)
        self.socketList.append(socket)
        return socket

    def saveSockets(self):
        sockets = list()
        for socket in self.socketList:
            sockets.append(socket.onSave())
        return sockets

    def loadSockets(self, sockets):
        if(self.isTriggerComponent is True):
            self.genTriggerSocket()
        index = 0
        for socket in sockets:
            self.socketList[index].loadPacket(socket)

##### Hardware Widget Interactions #####

    def registeriViewComponent(self, component):
        self.iViewComponent = component

    def ROIRemove(self, eventPos):
        self.iM.currentInstrument.removeComponent(self)

##### Sequence Editor Widget #####

    def onSequencerDoubleClick(self, eventPos):
        self.sequencerEditWidget.move(eventPos + QPoint(2, 2))
        if(self.sequencerEditWidget.isHidden()):
            self.sequencerEditWidget.updateTitle()
            self.sequencerEditWidget.show()
        else:
            self.sequencerEditWidget.hide()

    def loadSequenceData(self, events):
        if(self.sequencerEditWidget is None): #Generates this widget the first time it is made.
            self.sequencerEditWidget = sequenceEditWidget(self.mW, self)

        for event in events:
            self.sequencerEditWidget.addEvent(event)
        self.sequencerEditWidget.checkEventOverlaps()

        #self.Events_Modified.emit(self)
        self.iM.eventsMofieid(self)

##### Config Widget #####

    def hideConfigWindow(self):
        self.configWidget.hide()

    def updateConfigContent(self):
        pass

    def onLeftClick(self, eventPos):
        self.configWidget.move(eventPos + QPoint(2, 2))
        if(self.configWidget.isHidden()):
            self.updateConfigContent()
            self.configWidget.show()
        else:
            self.configWidget.hide()

class sequenceEditWidget(QDockWidget):
    doNotAutoPopulate = True
    Events_Modified = pyqtSignal(object)

    def __init__(self, mW, compParent):
        super().__init__('Sequencer: ' + compParent.compSettings['name'], parent=mW.sequencerDockWidget)
        self.compParent = compParent
        self.mW = mW
        self.iM = mW.iM
        self.sequencerWidget = self.compParent.mW.sequencerDockWidget
        self.setFeatures(QDockWidget.DockWidgetClosable)
        self.setMinimumSize(QSize(750,450))
        self.setFloating(True)
        self.hide()
        self.mainWidget = QWidget()
        self.layout = QVBoxLayout()
        self.mainWidget.setLayout(self.layout)
        self.sequencerEventTypes = compParent.sequencerEventTypes

        self.layout.addWidget(self.initTableWidget())
        self.layout.addWidget(self.initButtonsWidget())
        self.setWidget(self.mainWidget)

    def updateTitle(self):
        self.setWindowTitle('Sequence: ' + self.compParent.compSettings['name'])

    def clearEvents(self):
        #self.table.clear()
        for row in range(0, self.table.rowCount()):
            self.table.removeRow(0)

        #self.Events_Modified.emit(self)
        self.iM.eventsModified(self)

    def addEvent(self, eventData):
        newRow = self.newEvent()
        index = self.table.cellWidget(newRow, 1).findText(eventData['type'])
        if(index != -1):
            self.table.cellWidget(newRow, 0).setValue(eventData['time'])
            self.table.cellWidget(newRow, 1).setCurrentIndex(index)
            settingsWidgets = self.table.cellWidget(newRow, 2).stackWidgetDicts[index]
            for setting, value in eventData['settings'].items():
                if(setting in settingsWidgets):
                    settingsWidgets[setting].setValue(value)
                else:
                    self.compParent.mW.postLog('Event of type (' + eventData['type'] + ') does not have a (' + setting + ') setting type!!!', DSConstants.LOG_PRIORITY_HIGH)
        else:
            self.table.removeRow(newRow)
            self.compParent.mW.postLog('Event has unknown type (' + eventData['type'] + ') for object type (' + self.compParent.componentType + ')!!', DSConstants.LOG_PRIORITY_HIGH)
        
        #self.Events_Modified.emit(self)
        self.iM.eventsMofieid(self)

    def newEvent(self):
        rowCount = self.table.rowCount()
        self.table.insertRow(rowCount)
        if(rowCount > 0):
            s,e = self.getEventStartEnd(rowCount-1)
            time = e + 1
        else:
            time = 0
        timeWidget = timeInputEdit(rowCount, time=time)
        timeWidget.timeChanged.connect(self.sortEvent)
        timeWidget.timeChanged.connect(self.checkEventOverlaps)
        timeWidget.timeChanged.connect(self.eventsModified)

        self.table.setCellWidget(rowCount, 0, timeWidget)
        typeWidget = eventTypeComboBox(self.sequencerEventTypes)
        settingsWidget = eventSettingsEdit(self.sequencerEventTypes, rowCount)
        settingsWidget.parameterChanged.connect(self.checkEventOverlaps)
        settingsWidget.parameterChanged.connect(self.eventsModified)

        typeWidget.currentIndexChanged.connect(settingsWidget.redraw)
        typeWidget.currentIndexChanged.connect(self.checkEventOverlaps)
        typeWidget.currentIndexChanged.connect(self.eventsModified)

        self.table.setCellWidget(rowCount, 1, typeWidget)
        self.table.setCellWidget(rowCount, 2, settingsWidget)

        self.compParent.reprogramSourceTargets()

        #self.Events_Modified.emit(self)
        self.iM.eventsModified(self)

        return rowCount

    def eventsModified(self):
        #self.Events_Modified.emit(self)
        self.iM.eventsModified(self)

    def getEvents(self):
        eventListOut = list()
        for row in range(0, self.table.rowCount()):
            if(self.table.cellWidget(row, 0).valid is True):
                item = dict()
                item['time'] = self.table.cellWidget(row, 0).value()
                item['type'] = self.table.cellWidget(row, 1).value()
                item['settings'] = dict()
                for setting in self.table.cellWidget(row, 2).value():
                    item['settings'][setting.name] = setting.value()
                eventListOut.append(item)
        return eventListOut

    def getEventsSerializable(self):
        eventListOut = list()
        for row in range(0, self.table.rowCount()):
            item = dict()
            item['time'] = self.table.cellWidget(row, 0).value()
            item['type'] = self.table.cellWidget(row, 1).value().name
            item['settings'] = dict()
            for setting in self.table.cellWidget(row, 2).value():
                item['settings'][setting.name] = setting.value()
            eventListOut.append(item)
        return eventListOut

    def initTableWidget(self):
        self.table = QTableWidget(0,3)
        self.table.setHorizontalHeaderLabels(['Time (s)', 'Type', 'Settings'])
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 130)
        self.table.setColumnWidth(2, 500)
        #self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.itemSelectionChanged.connect(self.tableSelectionChanged)

        #self.model = QStandardItemModel(1, 3, self)
        #self.table.setModel(self.model)

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
        self.newEvent()

    def editButtonPressed(self):
        pass

    def removeButtonPressed(self):
        rows = self.getTableSelectedRows()
        for row in rows:
            self.table.removeRow(row)
        #self.Events_Modified.emit(self)
        self.iM.eventsModified(self)

    def getTableSelectedRows(self):
        indexes = self.table.selectedIndexes()
        rowList = list()
        for index in indexes:
            rowList.append(index.row())

        return rowList

    def getEventStartEnd(self, row):
        sequenceType = self.sequencerEventTypes[self.table.cellWidget(row, 2).stack.currentIndex()]
        params = self.table.cellWidget(row, 2).stack.currentWidget().paramList
        length = sequenceType.getLength(params)
        start = self.table.cellWidget(row, 0).value()
        end = start + length
        return start, end

    def checkEventOverlaps(self):
        for row in range(0, self.table.rowCount()):
            start, end = self.getEventStartEnd(row)
            result = self.checkIfTimeIsValid(row, start, end)
            if(result is False):
                self.table.cellWidget(row, 0).setBackground(QColor(Qt.red))
                self.table.cellWidget(row, 0).valid = False
                #widget = self.table.verticalHeaderItem(row)
                #widget.setBackground(QColor(255, 0, 0))
                #self.table.setVerticalHeaderItem(row, widget)
                #self.table.verticalHeaderItem(row).setBackground(QBrush(Qt.red))
            else:
                self.table.cellWidget(row, 0).setBackground(QColor(Qt.white))
                self.table.cellWidget(row, 0).valid = True
                #self.table.verticalHeaderItem(row).setBackground(QBrush(Qt.white))
        
        self.compParent.updatePlot()

    def setRowColor(self, row, color):
        self.table.cellWidget(row, 0).setBackground(color)
        #self.table.cellWidget(row, 2).setBackground(color)

    def checkIfTimeIsValid(self, index, startIn, endIn):
        for row in range(0, self.table.rowCount()):
            if(row != index):
                start, end = self.getEventStartEnd(row)
                if(start > startIn and start < endIn):
                    return False
                if(end > startIn and start < endIn):
                    return False
                if(startIn > start and startIn < end):
                    return False
                if(endIn > start and endIn < end):
                    return False
        return True

    def tableSelectionChanged(self):
        if(len(self.getTableSelectedRows()) > 0):
            self.editButton.setEnabled(True)
            self.removeButton.setEnabled(True)
        else:
            self.editButton.setEnabled(False)
            self.removeButton.setEnabled(False)

    def sortEvent(self, rowIn):
        rowTime = self.table.cellWidget(rowIn,0).value()
        lastValue = -99999
        for row in range(0, self.table.rowCount()):
            if(row != rowIn):
                curValue =  self.table.cellWidget(row,0).value()
                #print('BUTTER:'+str(lastValue)+':'+str(rowTime)+':'+str(curValue))
                if(rowTime > lastValue and rowTime <= curValue):
                    self.moveRow(rowIn, row)
                    return
                lastValue = curValue
        self.moveRow(rowIn, self.table.rowCount())

    def moveRow(self, row, target):
        if(row+1 == target):
            return
        widgetList = list()
        widgetList.append(self.table.cellWidget(row, 0))
        widgetList.append(self.table.cellWidget(row, 1))
        widgetList.append(self.table.cellWidget(row, 2))
        self.table.insertRow(target)
        self.table.setCellWidget(target, 0, widgetList[0])
        self.table.setCellWidget(target, 1, widgetList[1])
        self.table.setCellWidget(target, 2, widgetList[2])
        if(target < row):
            self.table.removeRow(row+1)
        else:
            self.table.removeRow(row)

        for row in range(0, self.table.rowCount()):
            self.table.cellWidget(row, 0).row = row
            self.table.cellWidget(row, 2).row = row

class timeInputEdit(QLineEdit):
    timeChanged = pyqtSignal(int)

    def __init__(self, row, decimalPlaces=4, time=0):
        super().__init__()
        self.row = row
        self.valid = True
        self.dirty = False
        self.setText(str(time))
        self.setValidator(QDoubleValidator())
        self.quant = Decimal(10) ** -decimalPlaces
        self.setStyleSheet("QLineEdit { qproperty-frame: false }")
        
        self.editingFinished.connect(self.checkValue)
        self.textEdited.connect(self.textHasChanged)
        self.dirty = False
        self.timeChanged.emit(self.row)

    def textHasChanged(self, value):
        self.dirty = True

    def isTextDirty(self):
        if(self.dirty is True):
            self.timeChanged.emit()
        self.dirty = False

    def setBackground(self, color):
        p = self.palette()
        p.setColor(self.backgroundRole(), color)
        self.setPalette(p)
        self.setStyleSheet("QLineEdit { qproperty-frame: false} QWidget { background: " + color.name() + "}")

    def value(self):
        return float(self.text())

    def setValue(self, value):
        self.setText(str(Decimal(value).quantize(self.quant)))

    def checkValue(self):
        value = self.text()
        self.setText(str(Decimal(value).quantize(self.quant)))
        if(self.dirty is True):
            self.timeChanged.emit(self.row)
        self.dirty = False

class eventSettingsEdit(QWidget):
    parameterChanged = pyqtSignal(int)

    def __init__(self, settingsType, row):
        super().__init__()
        self.settingsType = settingsType
        self.row = row
        self.index = 0
        self.stackList = list()
        self.stackWidgetDicts = list()
        self.stack = QStackedLayout()
        self.setLayout(self.stack)
        self.makeSettingsLayouts()
        self.initUI()
        self.setStyleSheet("QLineEdit { qproperty-frame: false }")

    def makeSettingsLayouts(self):
        for settingsType in self.settingsType:
            settingsList = list()
            widgetDict = dict()
            widget = settingsStackWidget()
            layout = QHBoxLayout()
            widget.setLayout(layout)
            for param in settingsType.genParameters():
                setting = settingsPair(param.name, param)
                settingsList.append(setting)
                label = QLabel(param.name+'=')
                label.setStyleSheet("QLabel {color: #425ff4}")
                layout.addWidget(label)
                layout.addWidget(param)
                widget.addParam(param)
                widgetDict[param.name] = param
                param.valueModified.connect(self.settingChanged)
            self.stack.addWidget(widget)
            self.stackList.append(settingsList)
            self.stackWidgetDicts.append(widgetDict)

    def value(self):
        return self.stackList[self.index]

    def settingChanged(self):
        self.parameterChanged.emit(self.row)

    def setBackground(self, color):
        self.setStyleSheet("QWidget {background: " + color.name() + "}")

    def redraw(self, index):
        self.index = index
        self.initUI()

    def initUI(self):
        self.stack.setCurrentIndex(self.index)

class settingsPair():
    def __init__(self, name, widget):
        self.name = name
        self.widget = widget

    def value(self):
        return self.widget.value()

class settingsStackWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.paramList = list()

    def addParam(self, param):
        self.paramList.append(param)

class eventTypeComboBox(QComboBox):
    def __init__(self, eventTypes):
        super().__init__()
        #self.addItem('')
        self.eventTypes = eventTypes
        for eventType in self.eventTypes:
            item = QComboBox
            self.addItem(eventType.name)

    def value(self):
        return self.eventTypes[self.currentIndex()]

class sequencerEventType():
    def __init__(self):
        self.name = 'DefaultEvent'
        self.parameters = list()

    def getLength(self, params):
        return 0

class eventParameter(QLineEdit):
    valueModified = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.name = ''
        self.editingFinished.connect(self.isTextDirty)
        self.textEdited.connect(self.textHasChanged)
        self.dirty = False

    def textHasChanged(self, value):
        self.dirty = True

    def isTextDirty(self):
        if(self.dirty is True):
            self.valueModified.emit()
        self.dirty = False

class eventParameterDouble(eventParameter):
    def __init__(self, name, defaultVal=0, decimalPlaces=4, allowZero=True, allowNegative=True, **kwargs):
        super().__init__()
        self.name = name
        self.allowZero = allowZero
        self.validator = QDoubleValidator()
        self.quant = Decimal(10) ** -decimalPlaces
        self.setValidator(self.validator)
        if(allowNegative == False):
            self.validator.setBottom(0)
        self.editingFinished.connect(self.checkValue)

        self.setText(str(defaultVal))
        self.editingFinished.emit()
        self.dirty = False

    def value(self):
        if(self.text() != '' and self.text() != '-' and self.text() != '.'):
            return float(self.text())
        else:
            return float(0.0)

    def setValue(self, value):
        self.setText(str(Decimal(value).quantize(self.quant)))

    def checkValue(self):
        value = self.text()
        if(self.allowZero is False):
            if(float(self.text()) == 0):
                value = '0.001'
        self.setText(str(Decimal(value).quantize(self.quant)))

class eventParameterInt(eventParameter):
    def __init__(self, name, defaultVal=0, allowZero=True, allowNegative=True, **kwargs):
        super().__init__()
        self.name = name
        self.allowZero = allowZero
        self.validator = QIntValidator()
        self.setValidator(self.validator)
        if(allowNegative == False):
            self.validator.setBottom(0)
        self.editingFinished.connect(self.checkValue)

        self.setText(str(defaultVal))
        self.editingFinished.emit()
        self.dirty = False

    def value(self):
        if(self.text() != ''):
            return int(self.text())
        else:
            return int(0)

    def setValue(self, value):
        self.setText(str(value))

    def checkValue(self):
        value = self.text()
        if(self.allowZero is False):
            if(float(self.text()) == 0):
                value = '1'
        self.setText(value)

class eventParameterString(eventParameter):
    def __init__(self, name, **kwargs):
        super().__init__()
        self.name = name
        self.dirty = False
        
    def value(self):
        return self.text()

    def setValue(self, value):
        self.setText(str(value))

class ComponentConfigWidget(QDockWidget):
    doNotAutoPopulate = True

    def __init__(self, compParent):
        super().__init__('Config: ' + compParent.name, parent=compParent.iM.instrumentWidget)
        self.compParent = compParent
        self.setFeatures(QDockWidget.DockWidgetClosable)
        self.setFloating(True)
        self.hide()

class ComponentSequenceEditWidget(QWidget):
    doNotAutoPopulate = True

    def __init__(self, component):
        super().__init__()
        self.component = component