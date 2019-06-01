from src.Managers.InstrumentManager.Component import *
from src.Managers.InstrumentManager.Sockets import *
from src.Managers.InstrumentManager.EventTypes import *
from src.Managers.HardwareManager.PacketCommands import *
import os, uuid
import numpy as np
import scipy.signal

class Deflection_Plate(Component):
    componentType = 'Deflection Plate'
    componentIdentifier = 'MRB_DefPlate'
    componentVersion = '1.0'
    componentCreator = 'Matthew R. Brantley'
    componentVersionDate = '5/30/2019'
    iconGraphicSrc = 'Trigger.png'
    valid = False

    def onCreation(self):
        self.compSettings['layoutGraphicSrc'] = self.iconGraphicSrc

        self.socket = self.addAOSocket(self.compSettings['name'])

        self.addEventType(chirpEvent)
        self.addEventType(sawWaveEvent)

    def onProgram(self):
        self.packet = commandPacket()
        v0 = 0
        for event in self.eventList:
            command = event.toCommand()
            self.packet.Add_Command(command)
        self.socket.Set_Programming_Packet(self.packet)

class sawWaveEvent(eventType):
    name = 'Sawtooth'

    def __init__(self):
        super().__init__()
        self.Add_Parameter(eventParameterInt('Count', allowZero=False, allowNegative=False, defaultVal=5))
        self.Add_Parameter(eventParameterDouble('Amplitude (V)', allowZero=False, allowNegative=False, defaultVal=1))
        self.Add_Parameter(eventParameterDouble('Cycle Length (ms)', allowZero=False, allowNegative=False, defaultVal=10))
        self.Add_Parameter(eventParameterInt('Sample Rate', allowZero=False, allowNegative=False, defaultVal=100000))
        
    def getLength(self):
        return (self.eventParams['Count'].v() * self.eventParams['Cycle Length (ms)'].v() / 1000)

    def toCommand(self):
        f = 1/(self.eventParams['Cycle Length (ms)'].v() / 1000)
        length = self.getLength()
        rate = self.eventParams['Sample Rate'].v()
        
        # t = np.linspace(self.time, self.time + length, rate)
        t = np.arange(self.time, self.time + length, 1/rate)
        s = scipy.signal.sawtooth(2 * np.pi * f * t) * self.eventParams['Amplitude (V)'].v()
        s = np.append(s, [[0], [0]])

        rate = self.eventParams['Sample Rate'].v()
        t0 = self.time
        command = AnalogWaveformCommand(t0, rate, s)
        return command


class chirpEvent(eventType):
    name = 'Chirp'

    def __init__(self):
        super().__init__()
        self.Add_Parameter(eventParameterDouble('Duration', allowZero=False, allowNegative=False, defaultVal=0.05))
        self.Add_Parameter(eventParameterDouble('Rate', allowZero=False, allowNegative=False, defaultVal=100000))
        self.Add_Parameter(eventParameterDouble('Start', allowZero=False, allowNegative=False, defaultVal=1000))
        self.Add_Parameter(eventParameterDouble('End', allowZero=False, allowNegative=False, defaultVal=10000))
        self.Add_Parameter(eventParameterDouble('Amplitude', allowZero=False, allowNegative=False, defaultVal=1))
    
    def getLength(self):
        return self.eventParams['Duration'].v()

    def toCommand(self):
        times = np.arange(self.time, self.time + self.eventParams['Duration'].v(), 1/self.eventParams['Rate'].v())
        wave = scipy.signal.chirp(times, self.eventParams['Start'].v(), times[-1], self.eventParams['End'].v())
        wave = np.multiply(wave, self.eventParams['Amplitude'].v())
        wave = np.append(wave, [[0], [0]])
        t0 = self.time
        f = self.eventParams['Rate'].v()
        command = AnalogWaveformCommand(t0, f, wave)
        return command