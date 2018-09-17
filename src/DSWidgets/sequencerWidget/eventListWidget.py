from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os, sys, imp, math, copy
from decimal import Decimal
from src.Constants import DSConstants as DSConstants

class eventListWidget(QDockWidget):
    doNotAutoPopulate = True

    def __init__(self, mW, sequencerWidget, comp):
        super().__init__('Sequencer: ' + comp.Get_Standard_Field('name'), parent=mW.sequencerDockWidget)
        self.comp = comp
        self.mW = mW
        self.iM = mW.iM
        self.sequencerWidget = sequencerWidget
        self.setFeatures(QDockWidget.DockWidgetClosable)
        self.setMinimumSize(QSize(750,450))
        self.setFloating(True)
        self.hide()
        self.mainWidget = QWidget()
        self.layout = QVBoxLayout()
        self.mainWidget.setLayout(self.layout)
        self.eventTypes = comp.Get_Event_Types()

        self.layout.addWidget(self.initTableWidget())
        self.layout.addWidget(self.initButtonsWidget())
        self.setWidget(self.mainWidget)

    def updateTitle(self):
        self.setWindowTitle('Sequence: ' + self.comp.Get_Standard_Field('name'))


    ######## THIS IS THE OLD IMPORT FUNCTION - NEED TO ADAPT
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
                    self.mW.postLog('Event of type (' + eventData['type'] + ') does not have a (' + setting + ') setting type!!!', DSConstants.LOG_PRIORITY_HIGH)
        else:
            self.table.removeRow(newRow)
            self.mW.postLog('Event has unknown type (' + eventData['type'] + ') for object type (' + type(self.comp) + ')!!', DSConstants.LOG_PRIORITY_HIGH)
        
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
        typeWidget = eventTypeComboBox(self.eventTypes)
        settingsWidget = eventSettingsEdit(self.eventTypes, rowCount)
        settingsWidget.parameterChanged.connect(self.checkEventOverlaps)
        settingsWidget.parameterChanged.connect(self.eventsModified)

        typeWidget.currentIndexChanged.connect(settingsWidget.redraw)
        typeWidget.currentIndexChanged.connect(self.checkEventOverlaps)
        typeWidget.currentIndexChanged.connect(self.eventsModified)

        self.table.setCellWidget(rowCount, 1, typeWidget)
        self.table.setCellWidget(rowCount, 2, settingsWidget)

        self.comp.reprogramSourceTargets()

        self.iM.eventsModified(self)

        return rowCount

    def savePacket(self):
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
        self.removeButton = QPushButton('Remove')
        self.removeButton.setEnabled(False)
        self.removeButton.pressed.connect(self.removeButtonPressed)

        self.buttonWidgetLayout.addWidget(self.addButton)
        self.buttonWidgetLayout.addWidget(self.removeButton)

        return self.buttonWidget

    def newButtonPressed(self):
        self.newEvent()

    def removeButtonPressed(self):
        rows = self.getTableSelectedRows()
        for row in rows:
            self.table.removeRow(row)
        self.iM.eventsModified(self)

    def getTableSelectedRows(self):
        indexes = self.table.selectedIndexes()
        rowList = list()
        for index in indexes:
            rowList.append(index.row())

        return rowList

    def tableSelectionChanged(self):
        if(self.getTableSelectedRows()):
            self.removeButton.setEnabled(True)
        else:
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

    def __init__(self, eventTypes, row):
        super().__init__()
        self.settingsType = eventTypes
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

class ComponentSequenceEditWidget(QWidget):
    doNotAutoPopulate = True

    def __init__(self, component):
        super().__init__()
        self.component = component
