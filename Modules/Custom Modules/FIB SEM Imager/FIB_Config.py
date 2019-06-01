from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import os

class FIB_Config(QWidget):
    def __init__(self, module):
        super().__init__(None)
        self.module = module
        self.ds = module.ds
        self.iM = module.ds.iM

        self.dirtyFlag = False

        self.targetInstrument = None
        self.targetXRaster = None
        self.targetYRaster = None
        self.targetDetector = None
        self.targetTrigger = None

        self.setupUI()

        self.iM.Instrument_Removed.connect(self.populateInstrumentList)
        self.iM.Instrument_New.connect(self.populateInstrumentList)
        self.iM.Instrument_Name_Changed.connect(self.populateInstrumentList)
        self.iM.Instrument_UUID_Changed.connect(self.populateInstrumentList)
        self.iM.Component_Added.connect(self.populateInstrumentList)
        self.iM.Component_Removed.connect(self.populateInstrumentList)

    def setupUI(self):
        self.layout = QFormLayout()

        self.instrumentSelection = QComboBox(self)
        self.instrumentSelection.setMinimumWidth(200)

        self.XRasterComponent = QComboBox(self)
        self.XRasterComponent.setMinimumWidth(200)

        self.YRasterComponent = QComboBox(self)
        self.YRasterComponent.setMinimumWidth(200)

        self.detectorComponent = QComboBox(self)
        self.detectorComponent.setMinimumWidth(200)

        self.triggerComponent = QComboBox(self)
        self.triggerComponent.setMinimumWidth(200)

        self.layout.addRow('Instrument: ', self.instrumentSelection)
        self.layout.addRow('    X Raster Component: ', self.XRasterComponent)
        self.layout.addRow('    Y Raster Component: ', self.YRasterComponent)
        self.layout.addRow('    Detector Component: ', self.detectorComponent)
        self.layout.addRow('    Trigger Component: ', self.triggerComponent)

        self.setLayout(self.layout)

        self.instrumentSelection.currentIndexChanged.connect(self.newInstrumentSelected)
        self.XRasterComponent.currentIndexChanged.connect(self.XRasterComponentSelected)
        self.YRasterComponent.currentIndexChanged.connect(self.YRasterComponentSelected)
        self.detectorComponent.currentIndexChanged.connect(self.detectorComponentSelected)
        self.triggerComponent.currentIndexChanged.connect(self.triggerComponentSelected)

        self.populateInstrumentList(None)
        self.newInstrumentSelected(self.instrumentSelection.currentIndex())

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
                    #self.targetInstrument = instruments[0]
                    self.instrumentSelection.setCurrentIndex(idx+1)
                    self.newInstrumentSelected(idx+1)
            # if(instr.Get_UUID() == instrument.Get_UUID()):
            #     self.instrumentSelection.setCurrentIndex(idx)
        
        if self.targetInstrument is None:
            self.instrumentSelection.setCurrentIndex(0)

    def newInstrumentSelected(self, index):
        self.XRasterComponent.clear()
        self.YRasterComponent.clear()
        self.detectorComponent.clear()
        self.triggerComponent.clear()

        XRaster_UUID = self.module.Read_Setting('XRasterComponent_UUID')
        YRaster_UUID = self.module.Read_Setting('YRasterComponent_UUID')
        DetectorComponent_UUID = self.module.Read_Setting('DetectorComponent_UUID')
        TriggerComponent_UUID = self.module.Read_Setting('TriggerComponent_UUID')

        uuid = self.instrumentSelection.itemData(index, role=Qt.UserRole)
        instrument = self.iM.Get_Instruments(uuid=uuid)

        if not instrument:
            instrument = None
        else:
            instrument = instrument[0]
            self.XRasterComponent.addItem('')
            self.YRasterComponent.addItem('')
            self.detectorComponent.addItem('')
            self.triggerComponent.addItem('')

            for idx, comp in enumerate(instrument.Get_Components()):
                self.XRasterComponent.addItem(comp.Get_Name())
                self.XRasterComponent.setItemData(idx+1, comp.Get_UUID(), role=Qt.UserRole)
                if comp.Get_UUID() == XRaster_UUID:
                    self.XRasterComponent.setCurrentIndex(idx+1)
                    self.XRasterComponentSelected(idx+1)

                self.YRasterComponent.addItem(comp.Get_Name())
                self.YRasterComponent.setItemData(idx+1, comp.Get_UUID(), role=Qt.UserRole)
                if comp.Get_UUID() == YRaster_UUID:
                    self.YRasterComponent.setCurrentIndex(idx+1)
                    self.YRasterComponentSelected(idx+1)

                self.detectorComponent.addItem(comp.Get_Name())
                self.detectorComponent.setItemData(idx+1, comp.Get_UUID(), role=Qt.UserRole)
                if comp.Get_UUID() == DetectorComponent_UUID:
                    self.detectorComponent.setCurrentIndex(idx+1)
                    self.detectorComponentSelected(idx+1)

                self.triggerComponent.addItem(comp.Get_Name())
                self.triggerComponent.setItemData(idx+1, comp.Get_UUID(), role=Qt.UserRole)
                if comp.Get_UUID() == TriggerComponent_UUID:
                    self.triggerComponent.setCurrentIndex(idx+1)
                    self.triggerComponentSelected(idx+1)

        self.targetInstrument = instrument
        
        self.updateConfig()

    def XRasterComponentSelected(self, index):
        uuid = self.XRasterComponent.itemData(index, role=Qt.UserRole)
        if self.targetInstrument:
            component = self.targetInstrument.Get_Components(uuid=uuid)

            if not component:
                self.targetXRaster = None
            else:
                self.targetXRaster = component[0]
                
        self.updateConfig()

    def YRasterComponentSelected(self, index):
        uuid = self.YRasterComponent.itemData(index, role=Qt.UserRole)
        if self.targetInstrument:
            component = self.targetInstrument.Get_Components(uuid=uuid)

            if not component:
                self.targetYRaster = None
            else:
                self.targetYRaster = component[0]

        self.updateConfig()

    def detectorComponentSelected(self, index):
        uuid = self.detectorComponent.itemData(index, role=Qt.UserRole)
        if self.targetInstrument:
            component = self.targetInstrument.Get_Components(uuid=uuid)

            if not component:
                self.targetDetector = None
            else:
                self.targetDetector = component[0]

        self.updateConfig()

    def triggerComponentSelected(self, index):
        uuid = self.triggerComponent.itemData(index, role=Qt.UserRole)
        if self.targetInstrument:
            component = self.targetInstrument.Get_Components(uuid=uuid)

            if not component:
                self.targetTrigger = None
            else:
                self.targetTrigger = component[0]

        self.updateConfig()

    def updateConfig(self):
        configData = {}
        configData['TargetInstrument'] = self.targetInstrument

        configData['XRasterComponent'] = self.targetXRaster
        configData['YRasterComponent'] = self.targetYRaster
        configData['DetectorComponent'] = self.targetDetector
        configData['TriggerComponent'] = self.targetTrigger

        if self.targetInstrument:
            self.module.Write_Setting('Instrument_UUID', self.targetInstrument.Get_UUID())
        if self.targetXRaster:
            self.module.Write_Setting('XRasterComponent_UUID', self.targetXRaster.Get_UUID())
        if self.targetYRaster:
            self.module.Write_Setting('YRasterComponent_UUID', self.targetYRaster.Get_UUID())
        if self.targetDetector:
            self.module.Write_Setting('DetectorComponent_UUID', self.targetDetector.Get_UUID())
        if self.targetTrigger:
            self.module.Write_Setting('TriggerComponent_UUID', self.targetTrigger.Get_UUID())

        self.module.updateProgramming(configData=configData)