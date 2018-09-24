from src.Managers.InstrumentManager.Component import *
from src.Managers.InstrumentManager.Sockets import *
from src.Managers.InstrumentManager.EventTypes import *
from src.Managers.HardwareManager.PacketCommands import *
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
    valid = False

    def onCreation(self):
        self.compSettings['name'] = 'Unnamed ' + self.componentType
        self.compSettings['layoutGraphicSrc'] = self.iconGraphicSrc

        self.socket = self.addAOSocket(self.compSettings['name'])

        self.addEventType(chirpEvent)

    def onProgram(self):
        self.packet = commandPacket()
        v0 = 0
        for event in self.eventList:
            command = event.toCommand()
            self.packet.Add_Command(command)
        self.socket.Set_Programming_Packet(self.packet)

class chirpEvent(eventType):
    name = 'Chirp'

    def __init__(self):
        super().__init__()
        self.Add_Parameter(eventParameterDouble('Duration'))
        self.Add_Parameter(eventParameterDouble('Duration', allowZero=False, allowNegative=False, defaultVal=0.05))
        self.Add_Parameter(eventParameterDouble('Rate', allowZero=False, allowNegative=False, defaultVal=100000))
        self.Add_Parameter(eventParameterDouble('Start', allowZero=False, allowNegative=False, defaultVal=1000))
        self.Add_Parameter(eventParameterDouble('End', allowZero=False, allowNegative=False, defaultVal=10000))
        self.Add_Parameter(eventParameterDouble('Amplitude', allowZero=False, allowNegative=False, defaultVal=1))
    
    def getLength(self, params):
        return 1

    def toCommand(self):
        times = np.arange(self.time, self.time + self.eventParams['Duration'].v(), 1/self.eventParams['Rate'].v())
        wave = scipy.signal.chirp(times, self.eventParams['Start'].v(), times[-1], self.eventParams['End'].v())
        t0 = self.time
        f = self.eventParams['Rate'].v()
        command = AnalogWaveformCommand(t0, f, wave)
        return command