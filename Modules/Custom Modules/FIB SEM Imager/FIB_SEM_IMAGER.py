from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os, random, numpy as np
from src.Constants import DSConstants as DSConstants, moduleFlags as mfs
from src.Managers.ModuleManager.DSModule import DSModule
from FIB_Settings import FIB_Settings
from FIB_Image_View import FIB_Image_View
from FIB_Config import FIB_Config

class FIB_SEM_IMAGER(DSModule):
    Module_Name = 'FIB SEM Imager'
    Module_Flags = [mfs.CAN_DELETE]

    def __init__(self, ds, handler):
        super().__init__(ds, handler)
        self.ds = ds
        self.iM = ds.iM

        self.progData = {}
        self.configData = {}

        self.setupUI()

        self.iM.Instrument_Ready_Checked.connect(self.instrumentReadyChecked)
        self.iM.Socket_Measurement_Packet_Recieved.connect(self.imageWidget.measurementPacketRecieved)

        self.updateProgramming()

    def setupUI(self):
        self.mainContainer = QMainWindow()

        self.settingsWidget = FIB_Settings(self)
        self.configWidget = FIB_Config(self)
        self.imageWidget = FIB_Image_View(self)

        self.tabWidget = QTabWidget()
        self.tabWidget.addTab(self.settingsWidget, 'Settings')
        self.tabWidget.addTab(self.configWidget, 'Config')

        self.mainSplitter = QSplitter()
        self.mainSplitter.addWidget(self.tabWidget)
        self.mainSplitter.addWidget(self.imageWidget)

        self.setWidget(self.mainContainer)
        self.mainContainer.setCentralWidget(self.mainSplitter)

        self.toolbar = QToolBar()
        self.initActions()
        self.initToolbar()
        self.mainContainer.addToolBar(self.toolbar)

    def initActions(self):
        self.saveImageAction = QAction('Save Image', self)
        self.saveImageAction.setShortcut('Ctrl+S')
        self.saveImageAction.setStatusTip('Save Current Image To Disk')
        self.saveImageAction.triggered.connect(self.saveImage)

        self.tabToggleAction = QToolButton(self)
        self.tabToggleAction.setIcon(QIcon(os.path.join(self.ds.srcDir, 'icons3\cogwheels.png')))
        self.tabToggleAction.setCheckable(True)
        self.tabToggleAction.setStatusTip('Show/Hide Settings')
        self.tabToggleAction.toggled.connect(self.tabToggled)
        self.tabToggleAction.toggle()

        self.collectAction = QToolButton(self)
        self.collectAction.setIcon(QIcon(os.path.join(self.ds.srcDir, 'icons2\photo-camera.png')))
        self.collectAction.setCheckable(True)
        self.collectAction.setStatusTip('Collect Images')
        #self.collectAction.toggle()

    def initToolbar(self):
        self.toolbar.addAction(self.saveImageAction)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.tabToggleAction)
        self.toolbar.addWidget(self.collectAction)

    def tabToggled(self, checked):
        if(checked):
            self.tabWidget.show()
        else:
            self.tabWidget.hide()

    def saveImage(self):
        print('SAVING IMAGE TO DISK?')

    def updateProgramming(self, progData=None, configData=None):
        if progData is not None:
            self.progData = progData
        if configData is not None:
            self.configData = configData

        if self.isReady():
            self.writeSequence()

    def instrumentReadyChecked(self, instrument):
        if instrument == self.configData['TargetInstrument']:
            if self.collectAction.isChecked():
                if instrument.Can_Run() is True:
                    instrument.Run_Instrument()

    def writeSequence(self):
        scanLength = self.progData['XResolution'] * (self.progData['Dwell Time']/1000)
        imageLength = scanLength * self.progData['YResolution']

        # X Raster
        self.configData['XRasterComponent'].Clear_Events()
        for eventType in self.configData['XRasterComponent'].Get_Event_Types():
            if eventType.name == 'Sawtooth':
                newEvent = eventType()
                for name, param in newEvent.Get_Parameters().items():
                    if name == 'Count':
                        param.setValue(self.progData['YResolution'])
                    if name == 'Amplitude (V)':
                        param.setValue(self.progData['XAmplitude'])
                    if name == 'Cycle Length (ms)':
                        param.setValue(scanLength)
                    if name == 'Sample Rate':
                        param.setValue(1000000)
                self.configData['XRasterComponent'].Add_Events(newEvent)

        # Y Raster
        self.configData['YRasterComponent'].Clear_Events()
        for eventType in self.configData['YRasterComponent'].Get_Event_Types():
            if eventType.name == 'Sawtooth':
                newEvent = eventType()
                for name, param in newEvent.Get_Parameters().items():
                    if name == 'Count':
                        param.setValue(1)
                    if name == 'Amplitude (V)':
                        param.setValue(self.progData['YAmplitude'])
                    if name == 'Cycle Length (ms)':
                        param.setValue(imageLength)
                    if name == 'Sample Rate':
                        param.setValue(1000000)
                self.configData['YRasterComponent'].Add_Events(newEvent)

        # Trigger
        self.configData['TriggerComponent'].Clear_Events()
        for eventType in self.configData['TriggerComponent'].Get_Event_Types():
            if eventType.name == 'Pulse':
                newEvent = eventType()
                newEvent.time = 0
                for name, param in newEvent.Get_Parameters().items():
                    if name == 'Voltage':
                        param.setValue(5)
                    if name == 'Duration':
                        param.setValue(0.005)
                self.configData['TriggerComponent'].Add_Events(newEvent)

        # Detector
        self.configData['DetectorComponent'].Clear_Events()
        offset = 1/self.progData['Dwell Time']
        for eventType in self.configData['DetectorComponent'].Get_Event_Types():
            if eventType.name == "N-Count Collection":
                newEvent = eventType()
                for name, param in newEvent.Get_Parameters().items():
                    if name == 'Num. Points':
                        param.setValue(int(imageLength/1000*1000000*offset))
                    if name == 'Rate':
                        param.setValue(1000000*offset)
                    if name == 'Range-Max':
                        param.setValue(10)
                    if name == 'Range-Min':
                        param.setValue(-10)
                self.configData['DetectorComponent'].Add_Events(newEvent)

    def isReady(self):
        if self.configData is None:
            return False
        if self.progData is None:
            return False

        try:
            if self.configData['TargetInstrument'] is None:
                return False
            if self.configData['XRasterComponent'] is None:
                return False
            if self.configData['YRasterComponent'] is None:
                return False
            if self.configData['DetectorComponent'] is None:
                return False
            if self.configData['TriggerComponent'] is None:
                return False

            if self.configData['XRasterComponent'] == self.configData['YRasterComponent']:
                return False
            if self.configData['XRasterComponent'] == self.configData['DetectorComponent']:
                return False
            if self.configData['XRasterComponent'] == self.configData['TriggerComponent']:
                return False
            if self.configData['YRasterComponent'] == self.configData['DetectorComponent']:
                return False
            if self.configData['YRasterComponent'] == self.configData['TriggerComponent']:
                return False
            if self.configData['DetectorComponent'] == self.configData['TriggerComponent']:
                return False
        except:
            return False

        return True


