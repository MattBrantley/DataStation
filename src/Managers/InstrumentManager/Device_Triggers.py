from src.Managers.InstrumentManager.Component import *
from src.Managers.InstrumentManager.Sockets import *
from src.Managers.InstrumentManager.EventTypes import *
from src.Managers.HardwareManager.PacketCommands import *
import os, uuid

class Device_Digital_Trigger(Component):
    componentType = 'Device Digital Trigger'
    componentIdentifier = 'dev_dig_trig'
    componentVersion = '1.0'
    componentCreator = 'Matthew R. Brantley'
    componentVersionDate = '11/14/2018'
    valid = False

    def onCreation(self):
        self.compSettings['name'] = 'Device Digital Trigger'

        self.socket = self.addDOSocket(self.compSettings['name'])

        self.addEventType(pulse)

    def onProgram(self):
        self.packet = commandPacket()
        v0 = 0
        for event in self.eventList:
            command = event.toCommand()
            self.packet.Add_Command(command)
        self.socket.Set_Programming_Packet(self.packet)

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