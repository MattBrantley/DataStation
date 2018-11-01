from PyQt5.Qt import *
from PyQt5.QtGui import QColor
import PyQt5.QtCore as QtCore
import json as json
import os, time
from src.Managers.ModuleManager.DSModule import DSModule
from src.Constants import DSConstants as DSConstants
from src.Constants import moduleFlags as mfs
from pathlib import Path

class SimpleInstrumentControl(DSModule):
    Module_Name = 'Simple Instrument Control'
    Module_Flags = [mfs.CAN_DELETE]

    STATUS_NOT_READY = 200
    STATUS_READY = 201
    STATUS_CONFIGURING = 202
    STATUS_RUNNING = 203
    STATUS_PROCESSING = 204
    STATUS_UNKNOWN = 205
    STATUS_WAITING = 206
    STATUS_READY_CHECKING = 207

    def __init__(self, ds, handler):
        super().__init__(ds, handler)
        self.ds = ds
        self.iM = ds.iM
        self.hM = ds.hM
        self.readyCheckMessages = list()
        self.targetUUID = None
        self.targetPath = None
        self.targetInstrument = None

        self.mainLayout = QHBoxLayout()
        self.mainWidget = QWidget()
        self.mainWidget.setLayout(self.mainLayout)
        self.setWidget(self.mainWidget)

        self.initButtons()

        self.instrumentSelectionBox = QComboBox()
        self.instrumentSelectionBox.setMinimumWidth(200)
        self.instrumentSelectionBox.currentIndexChanged.connect(self.instrumentSelectionChanged)

        self.mainLayout.addWidget(self.runOnceButton)
        self.mainLayout.addWidget(self.runMultipleButton)
        self.mainLayout.addWidget(self.runStopButton)
        self.mainLayout.addWidget(self.runSettingsButton)
        self.mainLayout.addWidget(self.instrumentSelectionBox)

        self.mainLayout.addStretch()
        self.mainLayout.addWidget(QLabel("Status:"))
        self.mainLayout.addWidget(self.statusDisplayWidget)
        self.mainLayout.addWidget(self.recheckReadyButton)
        self.mainLayout.addWidget(self.readyCheckInfoButton)

        self.setStatus(DSConstants.STATUS_NOT_READY)

        self.iM.Sequence_Loaded.connect(self.readyChecks)
        self.iM.Instrument_New.connect(self.readyChecks)
        self.iM.Socket_Attached.connect(self.readyChecks)

        self.iM.Instrument_Removed.connect(self.populateInstrumentList)
        self.iM.Instrument_New.connect(self.populateInstrumentList)
        self.iM.Instrument_Name_Changed.connect(self.populateInstrumentList)

        self.startReadyCheckTimer()
        self.populateInstrumentList()

    def populateInstrumentList(self):
        self.instrumentSelectionBox.clear()
        self.instrumentSelectionBox.addItem('')
        for idx, instrument in enumerate(self.iM.Get_Instruments()):
            self.instrumentSelectionBox.addItem(instrument.Get_Name())
            self.instrumentSelectionBox.setItemData(idx+1, instrument.Get_UUID(), role=Qt.UserRole)
            if(instrument.Get_UUID() == self.targetUUID):
                self.instrumentSelectionBox.setCurrentIndex(idx+1)

    def instrumentSelectionChanged(self, index):
        uuid = self.instrumentSelectionBox.itemData(index, role=Qt.UserRole)
        instrument = self.iM.Get_Instruments(uuid=uuid)

        if not instrument:
            instrument = None
        else:
            instrument = instrument[0]

        self.targetInstrument = instrument

        if(instrument is not None):
            self.setWindowTitle('Instrument Control (' + instrument.Get_Name() + ')')
            self.Write_Setting('Instrument_Path', instrument.Get_Path())

        else:
            self.setWindowTitle('Instrument Control (None)')
            self.Write_Setting('Instrument_Path', None)


    def startReadyCheckTimer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.configChanged)
        self.timer.start(10)

    def initButtons(self):
        dir = self.ds.srcDir
        self.runOnceButton = QPushButton()
        self.runOnceIcon = QIcon(os.path.join(dir, 'icons5\\reply.png'))
        self.runOnceButton.setIcon(self.runOnceIcon)
        self.runOnceButton.setIconSize(QSize(24,24))
        self.runOnceButton.pressed.connect(self.runOncePressed)

        self.runMultipleButton = QPushButton()
        self.runMultipleIcon = QIcon(os.path.join(dir, 'icons5\\reply-1.png'))
        self.runMultipleButton.setIcon(self.runMultipleIcon)
        self.runMultipleButton.setIconSize(QSize(24,24))
        self.runMultipleButton.pressed.connect(self.runMultiplePressed)
        self.runMultipleButton.setEnabled(False)

        self.runStopButton = QPushButton()
        self.runStopIcon = QIcon(os.path.join(dir, 'icons5\stop.png'))
        self.runStopButton.setIcon(self.runStopIcon)
        self.runStopButton.setIconSize(QSize(24,24))
        self.runStopButton.pressed.connect(self.runStopPressed)
        self.runStopButton.setEnabled(False)

        self.runSettingsButton = QPushButton()
        self.runSettingsIcon = QIcon(os.path.join(dir, 'icons5\settings.png'))
        self.runSettingsButton.setIcon(self.runSettingsIcon)
        self.runSettingsButton.setIconSize(QSize(24,24))
        self.runSettingsButton.pressed.connect(self.runSettingsPressed)
        self.runSettingsButton.setEnabled(False)

        self.recheckReadyButton = QPushButton()
        self.recheckReadyIcon = QIcon(os.path.join(dir, 'icons5\\refresh.png'))
        self.recheckReadyButton.setIcon(self.recheckReadyIcon)
        self.recheckReadyButton.setIconSize(QSize(14,14))
        self.recheckReadyButton.pressed.connect(self.configChanged)

        self.readyCheckInfoButton = readyCheckButton(self)
        self.readyCheckInfoButton.pressed.connect(self.readyCheckInfoPressed)

        self.statusDisplayWidget = statusDisplayWidget(self)

    def runOncePressed(self):
        if(self.readyChecks()):
            self.hM.Run_Sequence()

    def addReadyCheckMessage(self, message):
        self.readyCheckMessages.append(message)

    def runMultiplePressed(self):
        print('run multiple')

    def runStopPressed(self):
        print('run stop')

    def runSettingsPressed(self):
        print('settings')

    def readyCheckInfoPressed(self):
        menu = QMenu()

        messageListAction = QWidgetAction(self)
        messageList = QListWidget(self)
        messageList.itemClicked.connect(self.readyCheckInfoSelectionChanged)
        messageList.setMinimumWidth(400)
        messageListAction.setDefaultWidget(messageList)

        #for message in self.readyCheckMessages:
        #    msgItem = QListWidgetItem(message.msg)
        #    if(message.status == DSConstants.READY_CHECK_ERROR):
        #        msgItem.setBackground(QColor(255, 70, 70))
        #    if(message.status == DSConstants.READY_CHECK_WARNING):
        #        msgItem.setBackground(QColor(255, 221, 173))
        #    messageList.addItem(msgItem)

        if self.targetInstrument is not None:
            for checkItem in self.targetInstrument.Ready_Check_List():
                msgItem = QListWidgetItem(checkItem['Msg'])
                msgItem.trace = checkItem['Trace']
                if(checkItem['Level'] == DSConstants.READY_CHECK_ERROR):
                    msgItem.setBackground(QColor(255, 70, 70))
                if(checkItem['Level'] == DSConstants.READY_CHECK_WARNING):
                    msgItem.setBackground(QColor(255, 221, 173))
                messageList.addItem(msgItem)                

        if(messageList.count() == 0):
            messageList.addItem("No Errors or Warnings Thrown")

        menu.addAction(messageListAction)
        action = menu.exec_(QCursor().pos())

    def readyCheckInfoSelectionChanged(self, item):
        menu = QMenu()
        traceAction = QWidgetAction(self)
        traceList = QListWidget(self)
        traceList.setMinimumWidth(500)
        traceAction.setDefaultWidget(traceList)

        headerItem = QListWidgetItem('STACK TRACE')
        headerItem.setBackground(QColor(255, 221, 173))
        traceList.addItem(headerItem)

        if(hasattr(item, 'trace')):
            for traceItem in item.trace:
                msgItem = QListWidgetItem(traceItem.Get_Name() + ': ' + traceItem.__str__())
                traceList.addItem(msgItem)

        menu.addAction(traceAction)
        action = menu.exec_(QCursor().pos())

    def configChanged(self):
        self.setStatus(DSConstants.STATUS_READY_CHECKING)
        if(self.statusDisplayWidget.status == DSConstants.STATUS_READY or self.statusDisplayWidget.status == DSConstants.STATUS_NOT_READY or self.statusDisplayWidget.status == DSConstants.STATUS_READY_CHECKING):
            if(self.readyChecks() is True):
                self.setStatus(DSConstants.STATUS_READY)
            else:
                self.setStatus(DSConstants.STATUS_NOT_READY)

    def readyChecks(self):
        self.readyCheckMessages.clear()
        ready = True

        if self.targetInstrument is None:
            return False
        else:
            self.targetInstrument.Ready_Check()
            if self.targetInstrument.Ready_Check_Status() is True:
                return True
            else:
                return False

        #iMResults = self.iM.Do_Ready_Check()
        #if(iMResults.readyStatus is DSConstants.READY_CHECK_ERROR):
        #    ready = False
        #for msg in iMResults.generateMessages(-1): 
        #    self.addReadyCheckMessage(msg)

        #hMResults = self.hM.Do_Ready_Check()
        #if(hMResults.readyStatus is DSConstants.READY_CHECK_ERROR):
        #    ready = False
        #for msg in hMResults.generateMessages(-1):
        #    self.addReadyCheckMessage(msg)

        #return ready

    def setStatus(self, state):
        self.statusDisplayWidget.changeStatus(state)
        self.updateButtons()

    def updateButtons(self):
        if(self.statusDisplayWidget.status == DSConstants.STATUS_NOT_READY):
            self.runOnceButton.setEnabled(False)
            self.runMultipleButton.setEnabled(False)
            self.runStopButton.setEnabled(False)
            self.runSettingsButton.setEnabled(True)
            self.readyCheckInfoButton.setToError()

        if(self.statusDisplayWidget.status == DSConstants.STATUS_READY):
            self.runOnceButton.setEnabled(True)
            self.runMultipleButton.setEnabled(True)
            self.runStopButton.setEnabled(False)
            self.runSettingsButton.setEnabled(True)
            self.readyCheckInfoButton.setToInfo()

        if(self.statusDisplayWidget.status == DSConstants.STATUS_CONFIGURING):
            self.runOnceButton.setEnabled(False)
            self.runMultipleButton.setEnabled(False)
            self.runStopButton.setEnabled(False)
            self.runSettingsButton.setEnabled(False)
            self.readyCheckInfoButton.setToInfo()

        if(self.statusDisplayWidget.status == DSConstants.STATUS_RUNNING):
            self.runOnceButton.setEnabled(False)
            self.runMultipleButton.setEnabled(False)
            self.runStopButton.setEnabled(False)
            self.runSettingsButton.setEnabled(False)
            self.readyCheckInfoButton.setToInfo()

        if(self.statusDisplayWidget.status == DSConstants.STATUS_PROCESSING):
            self.runOnceButton.setEnabled(False)
            self.runMultipleButton.setEnabled(False)
            self.runStopButton.setEnabled(False)
            self.runSettingsButton.setEnabled(False)
            self.readyCheckInfoButton.setToInfo()

        if(self.statusDisplayWidget.status == DSConstants.STATUS_WAITING):
            self.runOnceButton.setEnabled(False)
            self.runMultipleButton.setEnabled(False)
            self.runStopButton.setEnabled(False)
            self.runSettingsButton.setEnabled(False)
            self.readyCheckInfoButton.setToInfo()

        if(self.statusDisplayWidget.status == DSConstants.STATUS_READY_CHECKING):
            self.runOnceButton.setEnabled(False)
            self.runMultipleButton.setEnabled(False)
            self.runStopButton.setEnabled(False)
            self.runSettingsButton.setEnabled(False)
            self.readyCheckInfoButton.setToInfo()

        self.readyCheckInfoButton.setMessageCount(len(self.readyCheckMessages))

class readyCheckButton(QPushButton):
    def __init__(self, controlWidget):
        super().__init__()
        dir = controlWidget.ds.srcDir
        self.messageCount = 0
        self.readyCheckInfoIcon = QIcon(os.path.join(dir, 'icons5\information.png'))
        self.readyCheckErrorIcon = QIcon(os.path.join(dir, 'icons5\warning.png'))
        self.setIcon(self.readyCheckInfoIcon)
        self.setIconSize(QSize(14, 14))

    def setToError(self):
        self.setIcon(self.readyCheckErrorIcon)

    def setToInfo(self):
        self.setIcon(self.readyCheckInfoIcon)

    def setMessageCount(self, count):
        self.messageCount = count

class statusDisplayWidget(QLineEdit):

    def __init__(self, controlWidget):
        super().__init__()
        self.setReadOnly(True)
        self.status = DSConstants.STATUS_NOT_READY
        self.changeStatus(DSConstants.STATUS_NOT_READY)
        
    def changeStatus(self, requestedStatus):
        self.status = requestedStatus
        self.updateText()

    def updateText(self):
        if(self.status == DSConstants.STATUS_NOT_READY):
            self.setStyleSheet("background-color: #DDDDDD; color: #ff0000")
            self.setText('NOT READY')
            return
        if(self.status == DSConstants.STATUS_READY):
            self.setStyleSheet("background-color: #DDDDDD; color: #007710; font-weight: bold")
            self.setText('READY')
            return
        if(self.status == DSConstants.STATUS_CONFIGURING):
            self.setText('CONFIGURING..')
            return
        if(self.status == DSConstants.STATUS_RUNNING):
            self.setText('RUNNING..')
            return
        if(self.status == DSConstants.STATUS_PROCESSING):
            self.setText('PROCESSING..')
            return
        if(self.status == DSConstants.STATUS_WAITING):
            self.setText('WAITING..')
            return
        if(self.status == DSConstants.STATUS_READY_CHECKING):
            self.setText('READY CHECKING..')
            return
            
        self.setText('UNKNOWN!')