from Managers.InstrumentManager.Component import *
from Managers.InstrumentManager.Sockets import *
import os, uuid
import numpy as np
import scipy.signal

class Excitation_Plates(Component):
    componentType = 'Excitation Plates'
    componentIdentifier = 'excPlates_mrb'
    componentVersion = '1.0'
    componentCreator = 'Matthew R. Brantley'
    componentVersionDate = '7/26/2018'
    iconGraphicSrc = 'Excitation_Plates.png'
    valid = True

    def onCreation(self):
        self.compSettings['name'] = 'Unnamed ' + self.componentType
        self.compSettings['layoutGraphicSrc'] = self.iconGraphicSrc
        self.compSettings['showSequencer'] = True
        self.compSettings['uuid'] = str(uuid.uuid4())

        self.socket = self.addAOSocket(self.compSettings['name'])

        self.addSequencerEventType(chirpEvent())

    def onRun(self):
        dataPacket = waveformPacket(self.data)
        self.setPathDataPacket(1, dataPacket)
        return True

    def parseSequenceEvents(self, events):
        self.data = None
        self.plotFrequency = 1e4
        lastEventTimeEnd = 0
        for event in events:
            newEventData = None

            #this is to help with the subsampling, zero points were being removed leading to odd lines when zoomed out
            gapX = np.arange(lastEventTimeEnd, event['time']-0.001, 0.001)
            gapY = np.zeros(len(gapX))
            gap = np.vstack((gapX, gapY)).transpose()


            if(isinstance(event['type'], chirpEvent) is True):
                points = event['settings']['Rate']*event['settings']['Duration']
                xAxisR = np.linspace(0, event['settings']['Duration'], points)
                xAxis = np.add(xAxisR, event['time'])
                yAxis = scipy.signal.chirp(xAxisR, event['settings']['Start'], event['settings']['Duration'], event['settings']['End'])
                yAxis = np.multiply(yAxis, event['settings']['Amplitude'])

                data = np.vstack((xAxis, yAxis)).transpose()   
                newEventData = np.vstack((np.array([event['time'], 0]), 
                    data, 
                    (np.array([event['time']+event['settings']['Duration'], 0]))))

                lastEventTimeEnd = event['time']+event['settings']['Duration']



            if(newEventData is not None):
                newEventData = np.vstack((gap, newEventData))
                if(self.data is None):
                    self.data = newEventData
                else:
                    self.data = np.vstack((self.data, newEventData))
            
        return self.data

    def plotSequencer(self, events):
        return self.parseSequenceEvents(events)


class chirpEvent(sequencerEventType):
    def __init__(self):
        super().__init__()
        self.name = 'Chirp'

    def genParameters(self):
        paramList = list()
        paramList.append(eventParameterDouble('Duration', allowZero=False, allowNegative=False, defaultVal=0.5))
        paramList.append(eventParameterDouble('Rate', allowZero=False, allowNegative=False, defaultVal=100000))
        paramList.append(eventParameterDouble('Start', allowZero=False, allowNegative=False, defaultVal=1000))
        paramList.append(eventParameterDouble('End', allowZero=False, allowNegative=False, defaultVal=10000))
        paramList.append(eventParameterDouble('Amplitude', allowZero=False, allowNegative=False, defaultVal=1))
        return paramList
    
    def getLength(self, params):
        return params[0].value()