from Managers.InstrumentManager.Component import *
from Managers.InstrumentManager.Sockets import *
import os, uuid

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

        self.addSequencerEventType(timedCollectionEvent())

    def onRun(self):
        dataPacket = waveformPacket(self.data)
        self.setPathDataPacket(1, dataPacket)
        return True

    def parseSequenceEvents(self, events):
        self.data = None
        return self.data

    def plotSequencer(self, events):
        return self.parseSequenceEvents(events)


class timedCollectionEvent(sequencerEventType):
    def __init__(self):
        super().__init__()
        self.name = 'Timed Collection'

    def genParameters(self):
        paramList = list()
        paramList.append(eventParameterDouble('Duration', allowZero=False, allowNegative=False))
        paramList.append(eventParameterDouble('Rate', allowZero=False, allowNegative=False))
        return paramList

    def getLength(self, params):
        return params[0].value()