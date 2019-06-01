from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os, random, numpy as np
from src.Constants import DSConstants as DSConstants, moduleFlags as mfs
from src.Managers.ModuleManager.DSModule import DSModule
from FT_AE_Config import FT_AE_Config
from FT_AE_Plot import FT_AE_Plot

class FT_Appearance_Energy(DSModule):
    Module_Name = 'FT Appearance Energy'
    Module_Flags = [mfs.CAN_DELETE]

    def __init__(self, ds, handler):
        super().__init__(ds, handler)
        self.ds = ds
        self.iM = ds.iM

        self.loading = False

        self.targetInstrument = None
        self.targetComponent = None
        self.eStart = 0
        self.eEnd = 100
        self.eStep = 10

        self.eCurrent = 0

        self.setupUI()

        self.iM.Instrument_Ready_Checked.connect(self.instrumentReadyChecked)
        # self.iM.Socket_Measurement_Packet_Recieved.connect(self.imageWidget.measurementPacketRevieced)

        self.loading=True

    def setupUI(self):
        self.mainContainer = QMainWindow()

        self.plotWidget = FT_AE_Plot(self)
        self.configWidget = FT_AE_Config(self)
        
        self.tabWidget = QTabWidget()
        self.tabWidget.addTab(self.plotWidget, 'Appearance Energy Plot')
        self.tabWidget.addTab(self.configWidget, 'Configuration')

        self.setWidget(self.mainContainer)
        self.mainContainer.setCentralWidget(self.tabWidget)

        self.toolbar = QToolBar()
        self.initActions()
        self.initToolbar()
        self.mainContainer.addToolBar(self.toolbar)

    def initActions(self):
        self.runAction = QAction('Run Experiment', self)
        self.runAction.setShortcut('Ctrl+S')
        self.runAction.setStatusTip('Save Current Image To Disk')
        self.runAction.triggered.connect(self.runActionPressed)

    def initToolbar(self):
        self.toolbar.addAction(self.runAction)

    def instrumentReadyChecked(self, instrument):
        if instrument == self.targetInstrument:
            if self.runAction.isChecked():
                if instrument.Can_Run() is True:
                    instrument.Run_Instrument()

    def runActionPressed(self):
        pass

    def updated(self):
        if self.isReady():
            self.writeSequence()

    def writeSequence(self):
        print('Writing Sequence!')

    def isReady(self):
        if self.targetInstrument is None:
            return False
        if self.targetComponent is None:
            return False

        if self.loading is False:
            return False

        return True