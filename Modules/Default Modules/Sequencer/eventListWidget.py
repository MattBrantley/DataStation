from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os, sys, imp, math, copy
from decimal import Decimal
from src.Managers.InstrumentManager.EventTypes import *

class eventListWidget(QDockWidget):
    doNotAutoPopulate = True
    STATUS_NO_CHANGE = 600
    STATUS_NEW = 601
    STATUS_MODIFIED = 602
    STATUS_REMOVED = 603
    STATUS_INVALID = 604

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

        self.iM.Sequence_Loaded.connect(self.refreshTable)
        self.iM.Sequence_Unloaded.connect(self.refreshTable)

    def updateTitle(self):
        self.setWindowTitle('Sequence: ' + self.comp.Get_Standard_Field('name'))

    def getEvents(self):
        for event in self.comp.Get_Events():
            self.newEvent(self.comp.Get_Instrument, self.comp, event)

    def newEvent(self, instrument=None, component=None, event=None):
        if(component is not self.comp):
            return #This ignores event calls for other components
        rowCount = self.table.rowCount()
        self.table.insertRow(rowCount)
        if(event is not None):
            time=event.time
            eventTextIn=event.name
            eventParams=event.eventParams
        else:
            if(rowCount > 0):
                time = rowCount
            else:
                time = 0
            eventTextIn=None
            eventParams=list()
        timeWidget = timeInputEdit(rowCount, time=time)
        timeWidget.timeChanged.connect(self.changeRowStatus)

        self.table.setCellWidget(rowCount, 0, timeWidget)
        
        typeWidget = eventTypeComboBox(rowCount, self.eventTypes, eventTextIn)
        settingsWidget = eventSettingsEdit(self.eventTypes, rowCount, event, params=eventParams, idx=typeWidget.currentIndex())
        settingsWidget.parameterChanged.connect(self.changeRowStatus)

        typeWidget.currentIndexChanged.connect(settingsWidget.eventTypeSelected)
        typeWidget.selectionChanged.connect(self.changeRowStatus)

        self.table.setCellWidget(rowCount, 1, typeWidget)
        self.table.setCellWidget(rowCount, 2, settingsWidget)
        if(instrument is None):
            self.changeRowStatus(rowCount, self.STATUS_NEW)
        else:
            self.changeRowStatus(rowCount, self.STATUS_NO_CHANGE)
        return rowCount

    def changeRowStatus(self, row, status):
        if(self.getRowStatus(row) == self.STATUS_NEW and status == self.STATUS_MODIFIED):
            return

        self.table.setItem(row, 3, QTableWidgetItem(str(status)))

        if(status == self.STATUS_NO_CHANGE):
            self.table.cellWidget(row, 0).setBackground(QColor(Qt.white))
        elif(status == self.STATUS_NEW):
            self.table.cellWidget(row, 0).setBackground(QColor(Qt.green))
        elif(status == self.STATUS_MODIFIED):
            self.table.cellWidget(row, 0).setBackground(QColor(Qt.blue))
        elif(status == self.STATUS_REMOVED):
            self.table.cellWidget(row, 0).setBackground(QColor(Qt.red))
        elif(status == self.STATUS_INVALID):
            self.table.cellWidget(row, 0).setBackground(QColor(Qt.gray))

    def refreshTable(self):
        self.clearTable()
        self.getEvents()

    def updateButtonPressed(self):
        eventSendList = list()
        for row in range(0, self.table.rowCount()):
            self.table.cellWidget(row, 2).eventBlueprint.time = self.table.cellWidget(row, 0).value()
            eventSendList.append([self.table.cellWidget(row, 2), self.getRowStatus(row), self.table.cellWidget(row, 2).eventIn])
        #self.clearTable() #The event data is now stored in eventSendList, this so that that the event signals don't get whiped.

        eventAddList = list()
        eventRemoveList = list()
        for event in eventSendList:
            if(event[1] == self.STATUS_NO_CHANGE):
                pass
            elif(event[1] == self.STATUS_NEW):
                eventAddList.append(event[0].value())
            elif(event[1] == self.STATUS_MODIFIED):
                eventRemoveList.append(event[2])
                eventAddList.append(event[0].value())
            elif(event[1] == self.STATUS_REMOVED):
                eventRemoveList.append(event[2])
            elif(event[1] == self.STATUS_INVALID):
                pass

        self.comp.Combined_Add_Remove_Events(eventAddList, eventRemoveList)

        self.refreshTable()

    def clearTable(self):
        self.table.clear()
        while(self.table.rowCount() > 0):
            self.table.removeRow(0)
        self.table.setHorizontalHeaderLabels(['Time (s)', 'Type', 'Settings', 'Status'])

    def initTableWidget(self):
        self.table = QTableWidget(0,4)
        self.table.setColumnHidden(3, True)
        self.table.setHorizontalHeaderLabels(['Time (s)', 'Type', 'Settings', 'Status'])
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 130)
        self.table.setColumnWidth(2, 500)
        #self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
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
        self.updateButton = QPushButton('Update')
        self.updateButton.pressed.connect(self.updateButtonPressed)
        self.updateButton.setEnabled(True)
        self.removeButton = QPushButton('Remove')
        self.removeButton.setEnabled(False)
        self.removeButton.pressed.connect(self.removeButtonPressed)

        self.buttonWidgetLayout.addWidget(self.addButton)
        self.buttonWidgetLayout.addWidget(self.updateButton)
        self.buttonWidgetLayout.addWidget(self.removeButton)

        return self.buttonWidget

    def newButtonPressed(self):
        self.newEvent(component=self.comp)

    def getRowStatus(self, row):
        if(self.table.item(row,3) is None):
            return False
        else:
            return int(self.table.item(row,3).text())

    def removeButtonPressed(self):
        rows = self.getTableSelectedRows()
        removeList = list()
        for row in rows:
            if(self.getRowStatus(row) == self.STATUS_NEW):
                removeList.append(row)
                continue
            self.changeRowStatus(row, self.STATUS_REMOVED)

        for row in reversed(removeList):
            self.table.removeRow(row)

    def getTableSelectedRows(self):
        indexes = self.table.selectedIndexes()
        rowList = list()
        for index in indexes:
            if(index.row() not in rowList):
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
    timeChanged = pyqtSignal(int, int)

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
        self.timeChanged.emit(self.row, 602)

    def textHasChanged(self, value):
        self.dirty = True

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
            self.timeChanged.emit(self.row, 602)
        self.dirty = False

class eventSettingsEdit(QWidget):
    parameterChanged = pyqtSignal(int, int)

    def __init__(self, eventTypes, row, eventIn, params=list(), idx=0):
        super().__init__()
        self.eventTypes = eventTypes
        self.row = row
        self.setStyleSheet("QLineEdit { qproperty-frame: false }")
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.params = params

        self.eventBlueprint = None
        self.eventIn = eventIn
        self.settingsPairList = list()
        
        self.eventTypeSelected(idx)

    def value(self):
        for pair in self.settingsPairList:
            self.eventBlueprint.eventParams[pair.name] = pair.param.value()
        return self.eventBlueprint

    def eventTypeSelected(self, index):
        if(self.eventTypes[index] is not None):
            self.eventBlueprint = self.eventTypes[index]()

            self.settingsPairList.clear()
            self.clearLayout(self.layout)

            for name, param in self.eventBlueprint.Get_Parameters().items():
                label = QLabel(name+'=')
                label.setStyleSheet("QLabel {color: #425ff4}")
                self.layout.addWidget(label)

                if(type(param) is eventParameterDouble):
                    widget = eventParameterWidgetDouble(param)
                elif(type(param) is eventParameterInt):
                    widget = eventParameterWidgetInt(param)
                elif(type(param) is eventParameterString):
                    widget = eventParameterWidgetString(param)

                if(name in self.params):
                    if(self.params[name].value() is not None):
                        widget.setValue(self.params[name].value())

                sPair = settingsPair(name, widget)
                self.settingsPairList.append(sPair)

                self.layout.addWidget(widget)
                widget.valueModified.connect(self.paramChanged)

    def clearLayout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                self.clearLayout(child.layout())

    def paramChanged(self):
        self.parameterChanged.emit(self.row, 602)


class settingsPair():
    def __init__(self, name, param):
        self.name = name
        self.param = param

    def value(self):
        return self.param.value()

class eventTypeComboBox(QComboBox):
    selectionChanged = pyqtSignal(int, int)
    def __init__(self, row, eventTypes, eventText):
        super().__init__()
        self.row = row
        #self.addItem('')
        self.eventTypes = eventTypes
        idx = 0
        for eventType in self.eventTypes:
            item = QComboBox
            self.addItem(eventType.name)
            if(eventType.name == eventText):
                self.setCurrentIndex(idx)
            idx += 1
        
        self.currentIndexChanged.connect(self.selChanged)

    def selChanged(self, idx):
        self.selectionChanged.emit(self.row, 602)

    def value(self):
        return self.eventTypes[self.currentIndex()]

##### Type Specific QLineEdit Widgets #####

class eventParameterWidget(QLineEdit):
    valueModified = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.name = ''
        self.dirty = True
        self.editingFinished.connect(self.updateValue)
        self.textEdited.connect(self.textHasChanged)

    def textHasChanged(self, value):
        self.dirty = True

    def updateValue(self):
        self.setValue(self.text())
        if(self.dirty is True):
            self.valueModified.emit()
        self.dirty = False

    def setValue(self, value):
        self.setText(value)

class eventParameterWidgetDouble(eventParameterWidget):
    def __init__(self, param): #, defaultVal=0, decimalPlaces=4, allowZero=True, allowNegative=True):
        super().__init__()
        self.param = param
        self.name = param.name
        self.validator = QDoubleValidator()
        self.quant = Decimal(10) ** -param.paramSettings['decimalPlaces']
        self.setValidator(self.validator)
        if(param.paramSettings['allowNegative'] == False):
            self.validator.setBottom(0)
        self.editingFinished.connect(self.checkValue)

        self.setText(str(param.paramSettings['defaultVal']))
        self.editingFinished.emit()

    def value(self):
        if(self.text() != '' and self.text() != '-' and self.text() != '.'):
            val = float(self.text())
        else:
            val = float(0.0)

        #paramOut = eventParameterDouble(self.name, defaultVal=self.defaultVal, decimalPlaces=self.decimalPlaces, allowZero=self.allowZero, allowNegative=self.allowNegative)
        self.param.setValue(val)
        return self.param

    def setValue(self, value):
        self.setText(str(Decimal(value).quantize(self.quant)))

    def checkValue(self):
        value = self.text()
        if(self.param.paramSettings['allowZero'] is False):
            if(float(self.text()) == 0):
                value = '0.001'
        self.setText(str(Decimal(value).quantize(self.quant)))

class eventParameterWidgetInt(eventParameterWidget):
    def __init__(self, param): # defaultVal=0, allowZero=True, allowNegative=True):
        super().__init__()
        self.param = param
        self.name = param.name
        self.validator = QIntValidator()
        self.setValidator(self.validator)
        if(param.paramSettings['allowNegative']  == False):
            self.validator.setBottom(0)
        self.editingFinished.connect(self.checkValue)

        self.setText(str(param.paramSettings['defaultVal']))
        self.editingFinished.emit()

    def value(self):
        if(self.text() != ''):
            val = int(self.text())
        else:
            val =  int(0)

        #paramOut = eventParameterInt(self.name, defaultVal=self.defaultVal, allowZero=self.allowZero, allowNegative=self.allowNegative)
        self.param.setValue(val)
        return self.param

    def setValue(self, value):
        self.setText(str(value))

    def checkValue(self):
        value = self.text()
        if(self.param.paramSettings['allowZero'] is False):
            if(float(self.text()) == 0):
                value = '1'
        self.setText(value)

class eventParameterWidgetString(eventParameterWidget):
    def __init__(self, param):
        super().__init__()
        self.param = param
        self.name = param.name
        
    def value(self):
        val =  self.text()
        #paramOut = eventParameterString(self.name)
        self.param.setValue(val)
        return self.param

    def setValue(self, value):
        self.setText(str(value))
