from Component import *
from src.Managers.InstrumentManager.Sockets import *
from src.Managers.InstrumentManager.EventTypes import *
from src.Managers.HardwareManager.PacketCommands import *
import os, uuid
import numpy as np
import scipy.signal

class Digital_Auto_Trigger(Component):
    componentType = 'Digital Auto Trigger'
    componentIdentifier = 'digi_auto_trig_mrb'
    componentVersion = '1.0'
    componentCreator = 'Matthew R. Brantley'
    componentVersionDate = '1/19/2019'
    iconGraphicSrc = 'Trigger.png'
    valid = False

    def onCreation(self):
        self.compSettings['layoutGraphicSrc'] = self.iconGraphicSrc

        self.socket = self.addDOSocket('Trigger Out')
        self.socket = self.addDISocket('Trigger In')

    def onProgram(self):
        self.packet = commandPacket()
        v0 = 0
        for event in self.eventList:
            command = event.toCommand()
            self.packet.Add_Command(command)
        self.socket.Set_Programming_Packet(self.packet)