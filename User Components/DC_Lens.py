# -*- coding: utf-8 -*-
"""
A simple DC Lens.
"""
from Component import *
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
        #self.data = self.randData()

        self.addSequencerEventType(stepEvent())
        self.addSequencerEventType(pulseEvent())
        self.addSequencerEventType(pulseTrainEvent())
        self.addSequencerEventType(linearRampEvent())

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

    def plotSequencer(self, events):
        data = None
        lastEventVoltage = 0
        for event in events:
            newEventData = None

            if(isinstance(event['type'], stepEvent) is True):
                newEventData = np.array([[event['time'], lastEventVoltage],
                [event['time']+0.000001, event['settings']['Voltage']]])

                lastEventVoltage = event['settings']['Voltage']
                #print(newEventData)

            if(isinstance(event['type'], pulseEvent) is True):
                newEventData = np.array([[event['time'], lastEventVoltage],
                [event['time'], event['settings']['Voltage']],
                [event['time']+event['settings']['Duration'], event['settings']['Voltage']],
                [event['time']+event['settings']['Duration'], lastEventVoltage]])

                lastEventVoltage = lastEventVoltage            
                
            if(isinstance(event['type'], pulseTrainEvent) is True):
                newEventData = None
                for n in range(0, event['settings']['Count']):
                    offset = n*event['settings']['offDuration'] + n*event['settings']['onDuration']
                    newEventStep = np.array([[event['time']+offset, lastEventVoltage],
                    [event['time']+offset, event['settings']['Voltage']],
                    [event['time']+event['settings']['onDuration']+offset, event['settings']['Voltage']],
                    [event['time']+event['settings']['onDuration']+offset, lastEventVoltage]])
                    if(newEventData is None):
                        newEventData = newEventStep
                    else:
                        newEventData = np.vstack((newEventData, newEventStep))

                lastEventVoltage = lastEventVoltage

            if(isinstance(event['type'], linearRampEvent) is True):
                duration = event['settings']['Duration']

                newEventData = np.array([[event['time'], lastEventVoltage],
                [event['time']+duration, event['settings']['Voltage']]])

                lastEventVoltage = event['settings']['Voltage']

            if(newEventData is not None):
                if(data is None):
                    data = newEventData
                else:
                    data = np.vstack((data, newEventData))
        #print(data)
        return data

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

class stepEvent(sequencerEventType):
    def __init__(self):
        super().__init__()
        self.name = 'Step'

    def genParameters(self):
        paramList = list()
        paramList.append(eventParameterDouble('Voltage'))
        return paramList

    def getLength(self, params):
        return 0.001

class pulseEvent(sequencerEventType):
    def __init__(self):
        super().__init__()
        self.name = 'Pulse'

    def genParameters(self):
        paramList = list()
        paramList.append(eventParameterDouble('Voltage'))
        paramList.append(eventParameterDouble('Duration', allowZero=False, allowNegative=False))
        return paramList

    def getLength(self, params):
        return params[1].value()

class linearRampEvent(sequencerEventType):
    def __init__(self):
        super().__init__()
        self.name = 'Linear Ramp'

    def genParameters(self):
        paramList = list()
        paramList.append(eventParameterDouble('Voltage'))
        paramList.append(eventParameterDouble('Duration', allowZero=False))
        return paramList

    def getLength(self, params):
        return params[1].value()

class pulseTrainEvent(sequencerEventType):
    def __init__(self):
        super().__init__()
        self.name = 'Pulse Train'

    def genParameters(self):
        paramList = list()
        paramList.append(eventParameterDouble('Voltage'))
        paramList.append(eventParameterInt('Count', allowZero=False, allowNegative=False))
        paramList.append(eventParameterDouble('onDuration', allowZero=False, allowNegative=False))
        paramList.append(eventParameterDouble('offDuration', allowZero=False, allowNegative=False))
        return paramList

    def getLength(self, params):
        return params[1].value()*params[2].value() + (params[1].value()-1)*params[3].value()

class DC_LensEvent():
    def __init__(self, time, eventType, data):
        self.time = time
        self.eventType = eventType
        self.data = data
