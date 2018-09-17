from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os, sys, imp, math, copy
from src.Constants import DSConstants as DSConstants

class eventListWidget(QDockWidget):
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
        self.iM.eventsModified(self)

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

class ComponentConfigWidget(QDockWidget):
    doNotAutoPopulate = True

    def __init__(self, compParent):
        super().__init__('Config: ' + compParent.name)
        self.compParent = compParent
        self.setFeatures(QDockWidget.DockWidgetClosable)
        self.setFloating(True)
        self.hide()

class ComponentSequenceEditWidget(QWidget):
    doNotAutoPopulate = True

    def __init__(self, component):
        super().__init__()
        self.component = component
