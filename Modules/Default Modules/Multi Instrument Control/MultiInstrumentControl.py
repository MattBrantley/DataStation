from PyQt5.Qt import *
from PyQt5.QtGui import QColor
import PyQt5.QtCore as QtCore
import json as json
import os, time
from src.Managers.ModuleManager.DSModule import DSModule
from src.Constants import DSConstants as DSConstants
from src.Constants import moduleFlags as mfs
from pathlib import Path

class MultiInstrumentControl(DSModule):
    Module_Name = 'Multi Instrument Control'
    Module_Flags = [mfs.CAN_DELETE]

    def __init__(self, ds, handler):
        super().__init__(ds, handler)
        self.ds = ds
        self.iM = ds.iM
        self.hM = ds.hM

        self.instrumentWidgetList = list()

        self.readyCheckMessages = list()

        self.mainLayout = QVBoxLayout()
        self.mainWidget = QWidget()
        self.mainWidget.setLayout(self.mainLayout)
        self.setWidget(self.mainWidget)

        #self.iM.Instrument_Removed.connect(self.updateInstrumentList)
        #self.iM.Instrument_Loaded.connect(self.populateInstrumentWidgets)
        self.iM.Instrument_New.connect(self.addInstrumentItem)
        self.iM.Instrument_Removed.connect(self.removedInstrumentItem)
        #self.iM.Instrument_Name_Changed.connect(self.populateInstrumentWidgets)

        self.populateInstrumentWidgets()

    def addInstrumentItem(self, instrument):
        newInstrumentWidget = instrumentControlItem(self.ds, instrument)
        self.instrumentWidgetList.append(newInstrumentWidget)
        self.mainLayout.addWidget(newInstrumentWidget)

    def removedInstrumentItem(self, instrument):
        for instrumentWidget in self.instrumentWidgetList:
            self.mainLayout.removeWidget(instrumentWidget)
            instrumentWidget.deleteLater()

        self.instrumentWidgetList.clear()

        self.populateInstrumentWidgets

    def populateInstrumentWidgets(self):
        for instrument in self.iM.Get_Instruments():
            self.addInstrumentItem(instrument)


class instrumentControlItem(QWidget):

    def __init__(self, ds, instrument):
        super().__init__()

        self.ds = ds
        self.iM = ds.iM
        self.targetInstrument = instrument
        self.readyCheckMessages = list()

        self.initLayout()

        self.iM.Instrument_Ready_Checked.connect(self.updateStatus)
        self.iM.Instrument_Name_Changed.connect(self.instrumentNameChanged)

    def instrumentNameChanged(self, instrument):
        if self.targetInstrument.Get_UUID() == instrument.Get_UUID():
            self.instrumentSelectionBox.clear()
            self.instrumentSelectionBox.addItem(self.targetInstrument.Get_Name())

    def getTargetUUID(self):
        return self.targetInstrument.Get_UUID()

    def initLayout(self):
        self.mainLayout = QHBoxLayout()
        self.setLayout(self.mainLayout)

        self.initButtons()

        self.instrumentSelectionBox = QComboBox()
        self.instrumentSelectionBox.setMinimumWidth(200)
        self.instrumentSelectionBox.addItem(self.targetInstrument.Get_Name())
        #self.instrumentSelectionBox.currentIndexChanged.connect(self.instrumentSelectionChanged)

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

        self.updateStatus(None)

        #self.startReadyCheckTimer()

    def initButtons(self):
        dir = self.ds.srcDir
        self.runOnceButton = QPushButton()
        self.runOnceIcon = QIcon(os.path.join(dir, 'icons5\\reply.png'))
        self.runOnceButton.setIcon(self.runOnceIcon)
        self.runOnceButton.setIconSize(QSize(24,24))
        self.runOnceButton.setToolTip('Run Once')
        self.runOnceButton.pressed.connect(self.runOncePressed)

        self.runMultipleButton = QPushButton()
        self.runMultipleIcon = QIcon(os.path.join(dir, 'icons5\\reply-1.png'))
        self.runMultipleButton.setIcon(self.runMultipleIcon)
        self.runMultipleButton.setIconSize(QSize(24,24))
        self.runMultipleButton.setToolTip('Rune Multiple')
        self.runMultipleButton.pressed.connect(self.runMultiplePressed)
        self.runMultipleButton.setEnabled(False)

        self.runStopButton = QPushButton()
        self.runStopIcon = QIcon(os.path.join(dir, 'icons5\stop.png'))
        self.runStopButton.setIcon(self.runStopIcon)
        self.runStopButton.setIconSize(QSize(24,24))
        self.runStopButton.setToolTip('Stop Run')
        self.runStopButton.pressed.connect(self.runStopPressed)
        self.runStopButton.setEnabled(False)

        self.runSettingsButton = QPushButton()
        self.runSettingsIcon = QIcon(os.path.join(dir, 'icons5\settings.png'))
        self.runSettingsButton.setIcon(self.runSettingsIcon)
        self.runSettingsButton.setIconSize(QSize(24,24))
        self.runSettingsButton.setToolTip('Settings')
        self.runSettingsButton.pressed.connect(self.runSettingsPressed)
        self.runSettingsButton.setEnabled(False)

        self.recheckReadyButton = QPushButton()
        self.recheckReadyIcon = QIcon(os.path.join(dir, 'icons5\\refresh.png'))
        self.recheckReadyButton.setIcon(self.recheckReadyIcon)
        self.recheckReadyButton.setIconSize(QSize(14,14))
        self.recheckReadyButton.setToolTip('Reset Instrument')
        self.recheckReadyButton.pressed.connect(self.resetPressed)

        self.readyCheckInfoButton = readyCheckButton(self)
        self.readyCheckInfoButton.pressed.connect(self.readyCheckInfoPressed)

        self.statusDisplayWidget = statusDisplayWidget(self)

    def runOncePressed(self):
        self.targetInstrument.Run_Instrument()

    def addReadyCheckMessage(self, message):
        self.readyCheckMessages.append(message)

    def runMultiplePressed(self):
        print('run multiple')

    def runStopPressed(self):
        self.targetInstrument.Stop_Instrument()

    def runSettingsPressed(self):
        menu = QMenu()
        settingsConfig = QWidgetAction(self.ds)
        settingsConfig.setDefaultWidget(settingsConfigWidget(self, self.ds))
        menu.addAction(settingsConfig)

        action = menu.exec_(QCursor().pos())

    def resetPressed(self):
        self.targetInstrument.Reset_Instrument()

    def readyCheckInfoPressed(self):
        menu = QMenu()

        messageListAction = QWidgetAction(self)
        messageList = QListWidget(self)
        messageList.itemClicked.connect(self.readyCheckInfoSelectionChanged)
        messageList.setMinimumWidth(400)
        messageListAction.setDefaultWidget(messageList)

        if self.targetInstrument is not None:
            for checkItem in self.targetInstrument.Ready_Check_List():
                msgItem = QListWidgetItem(checkItem['Msg'])
                msgItem.trace = checkItem['Trace']
                if(checkItem['Level'] == DSConstants.READY_CHECK_ERROR):
                    msgItem.setBackground(QColor(255, 70, 70))
                if(checkItem['Level'] == DSConstants.READY_CHECK_WARNING):
                    msgItem.setBackground(QColor(246, 255, 0))
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

    def updateStatus(self, instrument):
        if instrument == self.targetInstrument:
            readyCheckList = self.targetInstrument.Ready_Check_List()
            self.updateButtons(readyCheckList)
            self.statusDisplayWidget.update()

    def updateButtons(self, readyCheckList):
        if self.targetInstrument.Can_Run():
            self.runOnceButton.setEnabled(True)
            self.runMultipleButton.setEnabled(True)
        else:
            self.runOnceButton.setEnabled(False)
            self.runMultipleButton.setEnabled(False)

        if self.targetInstrument.Is_Running():
            self.runStopButton.setEnabled(True)
            self.runSettingsButton.setEnabled(True)
        else:
            self.runStopButton.setEnabled(False)
            self.runSettingsButton.setEnabled(False)

        readyCheckStatus = readyCheckList.Get_Status()

        if readyCheckStatus == DSConstants.READY_CHECK_ERROR:
            self.readyCheckInfoButton.setToError()
        elif readyCheckStatus == DSConstants.READY_CHECK_WARNING:
            self.readyCheckInfoButton.setToWarning()
        else:
            self.readyCheckInfoButton.setToInfo()

        self.readyCheckInfoButton.setMessageCount(len(readyCheckList))

class settingsConfigWidget(QWidget):
    def __init__(self, widget, ds):
        super().__init__()
        self.widget = widget
        self.ds = ds
        self.iM = ds.iM
        self.configLayout = QVBoxLayout()
        self.setLayout(self.configLayout)
        self.setMinimumWidth(200)

        self.backgroundInstrmentLabel = QLabel('Background Instrument:')
        self.configLayout.addWidget(self.backgroundInstrmentLabel)

        self.backgroundInstrumentBox = QComboBox()
        self.backgroundInstrumentBox.setMinimumWidth(200)

        self.configLayout.addWidget(self.backgroundInstrumentBox)
        
        self.backgroundSettingWidget = QWidget()
        self.backgroundSettingWidgetLayout = QFormLayout()
        self.backgroundSettingWidget.setLayout(self.backgroundSettingWidgetLayout)

        self.incrementBox = QSpinBox()
        self.incrementBox.setRange(250, 20000)
        self.backgroundSettingWidgetLayout.addRow('Interval (ms)', self.incrementBox)

        self.enabledBox = QCheckBox()
        self.backgroundSettingWidgetLayout.addRow('Enabled', self.enabledBox)

        self.configLayout.addWidget(self.backgroundSettingWidget)

class readyCheckButton(QPushButton):
    def __init__(self, controlWidget):
        super().__init__()
        dir = controlWidget.ds.srcDir
        self.messageCount = 0
        self.readyCheckInfoIcon = QIcon(os.path.join(dir, 'icons5\information.png'))
        self.readyCheckErrorIcon = QIcon(os.path.join(dir, 'icons5\warning.png'))
        self.readyCheckWarningIcon = QIcon(os.path.join(dir, 'icons5\warning2.png'))
        self.setIcon(self.readyCheckInfoIcon)
        self.setIconSize(QSize(14, 14))

    def setToWarning(self):
        self.setIcon(self.readyCheckWarningIcon)

    def setToError(self):
        self.setIcon(self.readyCheckErrorIcon)

    def setToInfo(self):
        self.setIcon(self.readyCheckInfoIcon)

    def setMessageCount(self, count):
        self.messageCount = count

class statusDisplayWidget(QLineEdit):

    def __init__(self, controlWidget):
        super().__init__()
        self.controlWidget = controlWidget
        self.messageIndex = 0
        self.messageList = list()
        self.setReadOnly(True)
        self.setText('NOT CONFIGURED..')
        self.startReadyCheckTimer()

    def startReadyCheckTimer(self):
        self.updateTimer = QTimer()
        self.updateTimer.timeout.connect(self.updateMessage)
        self.updateTimer.start(50)

        self.cycleTimer = QTimer()
        self.cycleTimer.timeout.connect(self.cycleMessage)
        self.cycleTimer.start(2000)

    def getPercentComplete(self):
        progress = self.controlWidget.targetInstrument.Get_Run_Time() / self.controlWidget.targetInstrument.Get_Sequence().Get_Sequence_Length() * 100
        if progress > 100:
            progress = 100

        return progress

    def updateMessage(self):
        messageCount = len(self.messageList)

        if self.controlWidget.targetInstrument.Is_Running():
            self.setStyleSheet("background-color: #DDDDDD; color: #007710; font-weight: bold")
            self.setText('Running!..  [' + str(int(self.getPercentComplete())) + '%]') 
            return

        if messageCount == 0:
            self.setStyleSheet("background-color: #DDDDDD; color: #007710; font-weight: bold")
            self.setText('READY')
            return

        if messageCount <= self.messageIndex:
            self.messageIndex = 0

        message = self.messageList[self.messageIndex]
        text = '[' + str(self.messageIndex + 1) + '/' + str(messageCount) + '] '

        if message['Level'] == DSConstants.READY_CHECK_ERROR:
            self.setStyleSheet("background-color: #DDDDDD; color: #ff0000; font-weight: bold")
            text = text + 'ERROR: '
        elif message['Level'] == DSConstants.READY_CHECK_WARNING:
            self.setStyleSheet("background-color: #DDDDDD; color: #AAAA00; font-weight: bold")
            text = text + 'WARNING: '
        else:
            self.setStyleSheet("background-color: #DDDDDD; color: #007710; font-weight: bold")

        text = text + message['Msg']
        self.setText(text)
        self.setCursorPosition(0)

    def cycleMessage(self):
        self.messageIndex += 1

    def update(self):
        self.messageList = self.controlWidget.targetInstrument.Ready_Check_List()
        self.updateMessage()