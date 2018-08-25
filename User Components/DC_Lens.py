# -*- coding: utf-8 -*-
"""
A simple DC Lens.
"""
from Component import Component
from PyQt5.Qt import *
from PyQt5.QtGui import *
import os, random
import numpy as np
from decimal import Decimal
from Sockets import *

class User_Component(Component):
    componentType = 'DC Lens'
    componentIdentifier = 'DCLens_MRB'
    componentVersion = '1.0'
    componentCreator = 'Matthew R. Brantley'
    componentVersionDate = '7/13/2018'
    iconGraphicSrc = 'Lens.png' #Not adjustable like layoutGraphicSrc
    valid = False

    def onCreation(self):
        self.compSettings['name'] = 'Unnamed ' + self.componentType
        self.compSettings['layoutGraphicSrc'] = self.iconGraphicSrc
        self.compSettings['vMin'] = 0.0
        self.compSettings['vMax'] = 10.0
        self.compSettings['showSequencer'] = True 
        self.sequenceEvents = list()
        self.containerWidget = self.configWidgetContent()
        self.configWidget.setWidget(self.containerWidget)
        self.addDCSocket(self.compSettings['name'])
        self.checkValidity()
        self.data = self.randData()

        self.addSequencerEventType('Step')
        self.addSequencerEventType('Ramp')
        self.addSequencerEventType('Pulse')

    def onRun(self):
        dataPacket = DCWaveformPacket(self.data)
        self.setPathDataPacket(1, dataPacket)
        return True

    def configWidgetContent(self):
        self.container = QWidget()
        self.fbox = QFormLayout()

        self.showSequenceBox = QCheckBox()
        self.showSequenceBox.setChecked(True)
        self.showSequenceBox.stateChanged.connect(self.saveWidgetValues)
        self.fbox.addRow("Draw Sequence:", self.showSequenceBox)

        self.nameBox = QLineEdit(self.compSettings['name'])
        self.nameBox.textChanged.connect(self.saveWidgetValues)
        self.fbox.addRow("Name:", self.nameBox)

        self.minVBox = QDoubleSpinBox()
        self.minVBox.setRange(-5000, 5000)
        self.minVBox.setValue(self.compSettings['vMin'])
        self.minVBox.valueChanged.connect(self.saveWidgetValues)
        self.fbox.addRow("Min (V):", self.minVBox)

        self.maxVBox = QDoubleSpinBox()
        self.maxVBox.setRange(-5000, 5000)
        self.maxVBox.setValue(self.compSettings['vMax'])
        self.maxVBox.valueChanged.connect(self.saveWidgetValues)
        self.fbox.addRow("Max (V):", self.maxVBox)

        self.container.setLayout(self.fbox)
        return self.container

    def randData(self):
        count = random.randint(1,100)
        var = random.randint(-5,10)
        newData = np.array([var-1,var])
        for i in range(count):
            data = np.array([var, random.randint(1,10)])
            var = var + 1
            newData = np.vstack((newData, data))
        return newData

    def plotSequencer(self):
        return self.data

    def saveWidgetValues(self):
        self.compSettings['showSequencer'] = self.showSequenceBox.isChecked()
        self.compSettings['name'] = self.nameBox.text()
        self.compSettings['vMin'] = self.minVBox.value()
        self.compSettings['vMax'] = self.maxVBox.value()
        self.checkValidity()

    def checkValidity(self):
        if(self.compSettings['vMax'] <= self.compSettings['vMin']):
            self.valid = False
            self.maxVBox.setStyleSheet("QDoubleSpinBox {background-color: red;}")
            self.minVBox.setStyleSheet("QDoubleSpinBox {background-color: red;}")
        else:
            self.valid = True
            self.maxVBox.setStyleSheet("QDoubleSpinBox {background-color: white;}")
            self.minVBox.setStyleSheet("QDoubleSpinBox {background-color: white;}")

class DC_LensEvent():
    def __init__(self, time, eventType, data):
        self.time = time
        self.eventType = eventType
        self.data = data
