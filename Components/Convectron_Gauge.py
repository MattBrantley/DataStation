from src.Managers.InstrumentManager.Component import *
from src.Managers.InstrumentManager.Sockets import *
from src.Managers.InstrumentManager.EventTypes import *
from src.Managers.HardwareManager.PacketCommands import *
import os, uuid
import numpy as np
import scipy.signal

class Convectron_Gauge(Component):
    componentType = 'Convectron Gauge'
    componentIdentifier = 'mrb_conv_gauge'
    componentVersion = '1.0'
    componentCreator = 'Matthew R. Brantley'
    componentVersionDate = '6/10/2019'
    iconGraphicSrc = 'Convectron.png'
    valid = False

    def onCreation(self):
        self.compSettings['layoutGraphicSrc'] = self.iconGraphicSrc

        self.socket = self.addAISocket('Voltage Input')

        self.addEventType(readOnce)

    def onProgram(self):
        self.packet = commandPacket()
        v0 = 0
        for event in self.eventList:
            command = event.toCommand()
            self.packet.Add_Command(command)
        self.socket.Set_Programming_Packet(self.packet)

class readOnce(eventType):
    name = 'readOnce'

    def __init__(self):
        super().__init__()
    
    def getLength(self):
        return 0

    def toCommand(self):
        command = AnalogAcquisitionCommand(1, 1, 10, 0)
        return command
