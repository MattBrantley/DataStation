from src.Managers.InstrumentManager.Component import *
from src.Managers.InstrumentManager.Sockets import *
from src.Managers.InstrumentManager.EventTypes import *
from src.Managers.HardwareManager.PacketCommands import *
import os, uuid
import numpy as np
import scipy.signal

class Basic_Trigger(Component):
    componentType = 'Basic Trigger'
    componentIdentifier = 'trig_mrb'
    componentVersion = '1.0'
    componentCreator = 'Matthew R. Brantley'
    componentVersionDate = '7/26/2018'
    iconGraphicSrc = 'Trigger.png'
    valid = False

    def onCreation(self):
        self.compSettings['layoutGraphicSrc'] = self.iconGraphicSrc

        self.socket = self.addDOSocket(self.compSettings['name'])

        self.addEventType(pulse)
        self.addEventType(goHigh)
        self.addEventType(goLow)

    def onProgram(self):
        self.packet = commandPacket()
        v0 = 0
        for event in self.eventList:
            command = event.toCommand()
            self.packet.Add_Command(command)
        self.socket.Set_Programming_Packet(self.packet)

class goHigh(eventType):
    name = 'Go High'

    def __init__(self):
        super().__init__()
    
    def getLength(self, params):
        return 1

    def toCommand(self):
        pairs = np.array([[self.time, 1]])
        command = DigitalSparseCommand(pairs)
        return command

class goLow(eventType):
    name = 'Go Low'

    def __init__(self):
        super().__init__()
    
    def getLength(self, params):
        return 1

    def toCommand(self):
        pairs = np.array([[self.time, 0]])
        command = DigitalSparseCommand(pairs)
        return command

class pulse(eventType):
    name = 'Pulse High'

    def __init__(self):
        super().__init__()
        self.Add_Parameter(eventParameterDouble('Width', allowZero=False, allowNegative=False, defaultVal=0.05))
    
    def getLength(self, params):
        return 1

    def toCommand(self):
        pairs = np.array([[self.time, 1], [self.time+self.eventParams['Width'].v(), 0]])
        command = DigitalSparseCommand(pairs)
        return command