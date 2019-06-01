from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import os

class FT_AE_Config(QWidget):
    def __init__(self, module):
        super().__init__(None)
        self.module = module
        self.ds = module.ds
        self.iM = module.ds.iM

        self.dirtyFlag = False

        self.setupUI()

        self.iM.Instrument_Removed.connect(self.populateInstrumentList)
        self.iM.Instrument_New.connect(self.populateInstrumentList)
        self.iM.Instrument_Name_Changed.connect(self.populateInstrumentList)
        self.iM.Instrument_UUID_Changed.connect(self.populateInstrumentList)
        # self.iM.Component_Added.connect(self.populateInstrumentList)
        # self.iM.Component_Removed.connect(self.populateInstrumentList)

    def setupUI(self):
        self.layout = QFormLayout()
        
        self.instrumentSelection = QComboBox(self)
        self.instrumentSelection.setMinimumWidth(200)

        self.componentSelection = QComboBox(self)
        self.componentSelection.setMinimumWidth(200)

        self.eStart = QLineEdit('0')
        self.eStart.setEnabled(True)
        self.eStartValidator = QDoubleValidator(0, 200, 0.1)
        self.eStart.setValidator(self.eStartValidator)

        self.eStop = QLineEdit('100')
        self.eStop.setEnabled(True)
        self.eStopValidator = QDoubleValidator(0, 200, 0.1)
        self.eStop.setValidator(self.eStopValidator)

        self.eStep = QLineEdit('10')
        self.eStep.setEnabled(True)
        self.eStepValidator = QDoubleValidator(0, 200, 0.1)
        self.eStep.setValidator(self.eStepValidator)

        self.layout.addRow('Instrument: ', self.instrumentSelection)
        self.layout.addRow('EI Component: ', self.componentSelection)
        self.layout.addRow('EI Energy Start: ', self.eStart)
        self.layout.addRow('EI Energy End: ', self.eStop)
        self.layout.addRow('EI Energy Step: ', self.eStep)

        self.setLayout(self.layout)

        self.updateUI()

        self.instrumentSelection.currentIndexChanged.connect(self.newInstrumentSelected)
        self.componentSelection.currentIndexChanged.connect(self.newComponentSelected)

        self.eStart.textChanged.connect(self.setDirtyFlag)
        self.eStop.textChanged.connect(self.setDirtyFlag)
        self.eStep.textChanged.connect(self.setDirtyFlag)

        self.eStart.editingFinished.connect(self.updateUI)
        self.eStop.editingFinished.connect(self.updateUI)
        self.eStep.editingFinished.connect(self.updateUI)

    def setDirtyFlag(self):
        self.dirtyFlag = True

    def updateUI(self):
        if self.dirtyFlag:
            self.module.eStart = float(self.eStart.text())
            self.module.eStop = float(self.eStop.text())
            self.module.eStep = float(self.eStep.text())

            self.dirtyFlag = False
            self.module.updated()

    def populateInstrumentList(self, instrument):
        Instrument_UUID = self.module.Read_Setting('Instrument_UUID')
        
        self.instrumentSelection.clear()
        self.instrumentSelection.addItem('')
        for idx, instr in enumerate(self.iM.Get_Instruments()):
            self.instrumentSelection.addItem(instr.Get_Name())
            self.instrumentSelection.setItemData(idx+1, instr.Get_UUID(), role=Qt.UserRole)
            if(instr.Get_UUID() == Instrument_UUID):
                instruments = self.iM.Get_Instruments(uuid=Instrument_UUID)
                if instruments:
                    self.instrumentSelection.setCurrentIndex(idx+1)
                    self.newInstrumentSelected(idx+1)

    def newInstrumentSelected(self, index):
        self.componentSelection.clear()
        self.setDirtyFlag()

        Component_UUID = self.module.Read_Setting('Component_UUID')

        uuid = self.instrumentSelection.itemData(index, role=Qt.UserRole)
        instrument = self.iM.Get_Instruments(uuid=uuid)

        if not instrument:
            instrument = None
        else:
            instrument = instrument[0]
            self.componentSelection.addItem('')

            for idx, comp in enumerate(instrument.Get_Components()):
                self.componentSelection.addItem(comp.Get_Name())
                self.componentSelection.setItemData(idx+1, comp.Get_UUID(), role=Qt.UserRole)
                if comp.Get_UUID() == Component_UUID:
                    self.componentSelection.setCurrentIndex(idx+1)
                    self.newComponentSelected(idx+1)

        self.module.targetInstrument = instrument

        if self.module.targetInstrument:
            self.module.Write_Setting('Instrument_UUID', self.module.targetInstrument.Get_UUID())

        self.updateUI()

    def newComponentSelected(self, index):
        self.setDirtyFlag()
        uuid = self.componentSelection.itemData(index, role=Qt.UserRole)
        if self.module.targetInstrument:
            component = self.module.targetInstrument.Get_Components(uuid=uuid)

            if not component:
                self.module.targetComponent = None
            else:
                self.module.targetComponent = component[0]

            if self.module.targetComponent:
                self.module.Write_Setting('Component_UUID', self.module.targetComponent.Get_UUID())
                    
            self.updateUI()
