from src.Managers.InstrumentManager.Component import *
from src.Managers.InstrumentManager.EventTypes import *
from src.Managers.InstrumentManager.Sockets import *
import os, uuid
import numpy as np

class Detection_Plates(Component):
    componentType = 'Detection Plates'
    componentIdentifier = 'detecPlates_mrb'
    componentVersion = '1.0'
    componentCreator = 'Matthew R. Brantley'
    componentVersionDate = '7/26/2018'
    iconGraphicSrc = 'Detection_Plates.png'
    valid = True
    
    def onCreation(self):
        self.compSettings['name'] = 'Unnamed ' + self.componentType
        self.compSettings['layoutGraphicSrc'] = self.iconGraphicSrc
        self.compSettings['showSequencer'] = True
        self.compSettings['uuid'] = str(uuid.uuid4())

        self.socket = self.addAISocket(self.compSettings['name'])

        self.addEventType(timedCollectionEvent)
        self.addEventType(nCountCollectionEvent)

    def onRun(self, events):
        self.parseSequenceEvents(events)
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


            if(isinstance(event['type'], timedCollectionEvent) is True):
                points = event['settings']['Duration']*self.plotFrequency
                xAxisR = np.linspace(0, event['settings']['Duration'], points)
                xAxis = np.add(xAxisR, event['time'])
                yAxisR = np.sin(np.multiply(xAxisR, self.plotFrequency))
                yAxisFilter = np.linspace(1, 0, points)
                yAxis = np.multiply(yAxisR, yAxisFilter)
                #print(xAxis.shape)
                data = np.vstack((xAxis, yAxis)).transpose()
                newEventData = np.vstack((np.array([event['time'], 0]), 
                    data, 
                    (np.array([event['time']+event['settings']['Duration'], 0]))))
                
                lastEventTimeEnd = event['time']+event['settings']['Duration']
                #print(newEventData.shape)
                #print(xAxis)

            if(isinstance(event['type'], nCountCollectionEvent) is True):
                dur = event['settings']['Num. Points']/event['settings']['Rate']
                points = dur*self.plotFrequency
                xAxisR = np.linspace(0, dur, points)
                xAxis = np.add(xAxisR, event['time'])
                yAxisR = np.sin(np.multiply(xAxisR, self.plotFrequency))
                yAxisFilter = np.linspace(1, 0, points)
                yAxis = np.multiply(yAxisR, yAxisFilter)
                #print(xAxis.shape)
                data = np.vstack((xAxis, yAxis)).transpose()
                newEventData = np.vstack((np.array([event['time'], 0]), 
                    data, 
                    (np.array([event['time']+dur, 0]))))
                lastEventTimeEnd = event['time']+dur


            if(newEventData is not None):
                newEventData = np.vstack((gap, newEventData))
                if(self.data is None):
                    self.data = newEventData
                else:
                    self.data = np.vstack((self.data, newEventData))
            
        return self.data

    def plotSequencer(self, events):
        return self.data


class timedCollectionEvent(eventType):
    def __init__(self):
        super().__init__()
        self.name = 'Timed Collection'

    def genParameters(self):
        paramList = list()
        paramList.append(eventParameterDouble('Duration', allowZero=False, allowNegative=False, defaultVal=0.5))
        paramList.append(eventParameterDouble('Rate', allowZero=False, allowNegative=False, defaultVal=10000))
        return paramList

    def getLength(self, params):
        return params[0].value()

class nCountCollectionEvent(eventType):
    def __init__(self):
        super().__init__()
        self.name = 'N-Count Collection'

    def genParameters(self):
        paramList = list()
        paramList.append(eventParameterInt('Num. Points', allowZero=False, allowNegative=False, defaultVal=5000))
        paramList.append(eventParameterDouble('Rate', allowZero=False, allowNegative=False, defaultVal=10000))
        return paramList

    def getLength(self, params):
        return params[0].value()/params[1].value()