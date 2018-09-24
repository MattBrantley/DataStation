# -*- coding: utf-8 -*-
"""
A simple DC Lens.
"""
from src.Managers.InstrumentManager.Component import *
from src.Managers.InstrumentManager.EventTypes import *
from src.Managers.InstrumentManager.Sockets import *
from src.Managers.HardwareManager.PacketCommands import *
from PyQt5.Qt import *
from PyQt5.QtGui import *
import os, random, numpy as np
from decimal import Decimal

class DC_Electrode(Component):
    componentType = 'DC Electrode'
    componentIdentifier = 'DCElec_MRB'
    componentVersion = '1.0'
    componentCreator = 'Matthew R. Brantley'
    componentVersionDate = '7/13/2018'
    iconGraphicSrc = 'default.png' #Not adjustable like layoutGraphicSrc
    valid = False

    def onCreation(self):
        self.compSettings['name'] = 'Unnamed ' + self.componentType
        self.compSettings['layoutGraphicSrc'] = self.iconGraphicSrc
        self.compSettings['vMin'] = 0.0
        self.compSettings['vMax'] = 10.0
        self.compSettings['granularity'] = 0.0001
        self.containerWidget = self.configWidgetContent()
        self.configWidget.setWidget(self.containerWidget)
        self.socket = self.addAOSocket(self.compSettings['name'])

        self.addEventType(stepEvent)
        self.addEventType(pulseEvent)
        self.addEventType(pulseTrainEvent)
        self.addEventType(linearRampEvent)

    def onProgram(self):
        self.packet = commandPacket()
        v0 = 0
        for event in self.eventList:
            command = event.toCommand(v0)
            self.packet.Add_Command(command)
            v0 = command.pairs[-1,1]
        self.socket.Set_Programming_Packet(self.packet)

    def updateConfigContent(self):
        self.showSequenceBox.setChecked(self.compSettings['showSequencer'])
        self.nameBox.setText(self.compSettings['name'])
        self.minVBox.setValue(self.compSettings['vMin'])
        self.maxVBox.setValue(self.compSettings['vMax'])

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

    def saveWidgetValues(self):
        self.compSettings['showSequencer'] = self.showSequenceBox.isChecked()
        self.compSettings['name'] = self.nameBox.text()
        self.compSettings['vMin'] = self.minVBox.value()
        self.compSettings['vMax'] = self.maxVBox.value()
        self.socket.name = self.compSettings['name']
        self.checkValidity()
        self.Component_Modified.emit(self)

class stepEvent(eventType):
    name = 'Step'

    def __init__(self):
        super().__init__()
        self.Add_Parameter(eventParameterDouble('Voltage'))

    def getLength(self, params):
        return self.gran

    def toCommand(self, v0):
        pairs = np.array([[self.time, v0], [self.time, self.eventParams['Voltage'].v()]])
        command = AnalogSparseCommand(pairs)
        return command

class pulseEvent(eventType):
    name = 'Pulse'
    def __init__(self):
        super().__init__()
        self.Add_Parameter(eventParameterDouble('Voltage'))
        self.Add_Parameter(eventParameterDouble('Duration', allowZero=False, allowNegative=False))

    def getLength(self, params):
        return params[1].value()

    def toCommand(self, v0):
        pairs = np.arange(self.time, self.time+self.eventParams['Duration']) 
        command = AnalogSparseCommand(pairs)
        return command

class linearRampEvent(eventType):
    name = 'Linear Ramp'

    def __init__(self):
        super().__init__()
        self.Add_Parameter(eventParameterDouble('Voltage'))
        self.Add_Parameter(eventParameterDouble('Duration', allowZero=False))

    def getLength(self, params):
        return params[1].value()

    def toCommand(self, v0):
        pairs = np.array([[self.time, v0],
        [self.time + self.eventParams['Duration'].v(), self.eventParams['Voltage'].v()]])
        command = AnalogSparseCommand(pairs)
        return command

class pulseTrainEvent(eventType):
    name = 'Pulse Train'
    
    def __init__(self):
        super().__init__()
        self.Add_Parameter(eventParameterDouble('Voltage'))
        self.Add_Parameter(eventParameterInt('Count', allowZero=False, allowNegative=False))
        self.Add_Parameter(eventParameterDouble('onDuration', allowZero=False, allowNegative=False))
        self.Add_Parameter(eventParameterDouble('offDuration', allowZero=False, allowNegative=False))

    def getLength(self, params):
        return params[1].value()*params[2].value() + (params[1].value()-1)*params[3].value()

    def toCommand(self, v0):
        pairs = None
        for n in range(0, self.eventParams['Count'].v()):
            offset = n * (self.eventParams['offDuration'].v() + self.eventParams['onDuration'].v())
            newEventStep = np.array([[self.time + offset, v0],
            [self.time + offset, self.eventParams['Voltage'].v()],
            [self.time + self.eventParams['onDuration'].v() + offset, self.eventParams['Voltage'].v()],
            [self.time + self.eventParams['onDuration'].v() + offset, v0]])
            if(pairs is None):
                pairs = newEventStep
            else:
                pairs = np.vstack((pairs, newEventStep))
        command = AnalogSparseCommand(pairs)
        return command