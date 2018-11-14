from src.Managers.InstrumentManager.Component import *
from src.Managers.InstrumentManager.Sockets import *
from src.Managers.InstrumentManager.EventTypes import *
from src.Managers.HardwareManager.PacketCommands import *
import os, uuid
import numpy as np
import scipy.signal

class Detection_Plates(Component):
    componentType = 'Detection Plates'
    componentIdentifier = 'detecPlates_mrb'
    componentVersion = '1.0'
    componentCreator = 'Matthew R. Brantley'
    componentVersionDate = '7/26/2018'
    iconGraphicSrc = 'Detection_Plates.png'
    valid = True
    
    def onCreation(self):
        self.compSettings['layoutGraphicSrc'] = self.iconGraphicSrc

        self.socket = self.addAISocket(self.compSettings['name'])

        self.addEventType(nCountCollectionEvent)

    def onProgram(self):
        self.packet = commandPacket()
        v0 = 0
        for event in self.eventList:
            command = event.toCommand()
            self.packet.Add_Command(command)
        self.socket.Set_Programming_Packet(self.packet)


class nCountCollectionEvent(eventType):
    name = 'N-Count Collection'

    def __init__(self):
        super().__init__()
        self.Add_Parameter(eventParameterInt('Num. Points', allowZero=False, allowNegative=False, defaultVal=5000))
        self.Add_Parameter(eventParameterDouble('Rate', allowZero=False, allowNegative=False, defaultVal=10000))
        self.Add_Parameter(eventParameterDouble('Range-Max', defaultVal=10))
        self.Add_Parameter(eventParameterDouble('Range-Min', defaultVal=-10))

    def getLength(self, params):
        return params[0].value()/params[1].value()

    def toCommand(self):
        command = AnalogAcquisitionCommand(self.eventParams['Rate'].v(), self.eventParams['Num. Points'].v(), self.eventParams['Range-Max'].v(), self.eventParams['Range-Min'].v())
        return command