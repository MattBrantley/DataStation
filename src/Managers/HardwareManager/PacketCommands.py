import numpy as np

class commandPacket():
############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################
    def Add_Command(self, command):
        self.commandList.append(command)

    def Remove_Command(self, command):
        self.commandList.remove(command)

    def Set_Origin_Socket(self, socket):
        self.originSocket = socket

    def Get_Origin_Socket(self):
        return self.originSocket

    def Get_Commands(self, commandType=None):
        return self.getCommands(commandType)

############################################################################################
#################################### INTERNAL USER ONLY ####################################
    def __init__(self):
        self.commandList = list()
        self.originSocket = None

    def getCommands(self, commandType=None):
        outList = list()
        for command in self.commandList:
            if(commandType is not None):
                if(issubclass(commandType, type(command)) is False):
                    continue

            outList.append(command)
        return outList

class Command():
    def __init__(self):
        pass

##### Digital Commands #####

class DigitalWaveformCommand(Command):
    def __init__(self, rate, yData):
        super().__init__()
        self.rate = rate
        self.yData = yData

class DigitalSparseCommand(Command):
    def __init__(self, pairs):
        super().__init__()
        self.pairs = pairs

class DigitalAcquisitionCommand(Command):
    def __init__(self, rate, noSamples):
        super().__init__()
        self.rate = rate
        self.noSamples = noSamples

##### Analog Commands #####

class AnalogWaveformCommand(Command):
    def __init__(self, t0, f, wave):
        super().__init__()
        self.t0 = t0
        self.f = f # is in units of Hertz (Hz)
        self.wave = wave # is in units of voltage (V)

    def count(self):
        return self.wave.shape[0]

    def toPairs(self):
        len = self.wave.shape[0]/self.f
        x = np.arange(self.t0, self.t0 + len, 1/self.f)
        y = self.wave
        res = np.vstack([x, y]).transpose()
        return res

class AnalogSparseCommand(Command):
    def __init__(self, pairs):
        super().__init__()
        self.pairs = pairs # numpy array: column 1 = time (second), column 2 = voltage (V)

class AnalogAcquisitionCommand(Command):
    ACQ_TRIG_EXTERNAL = 50
    ACQ_TRIG_THRESHOLD = 51

    def __init__(self, rate, noSamples, acqMax, acqMin, trig=ACQ_TRIG_EXTERNAL, trigThreshold=1, preTrigSamples=0):
        super().__init__()
        self.rate = rate # rate in units of Hertz (Hz)
        self.noSamples = noSamples
        self.acqMax = acqMax
        self.acqMin = acqMin
        self.trig = trig
        self.trigThreshold = trigThreshold # only used if trig=ACQ_TRIG_THRESHOLD, units in Voltage (V)
        self.preTrigSamples = preTrigSamples # the number of samples retained before the trigger event. 

##### Waveform Generator Commands #####

class WaveformCommand(Command):
    WFM_SINE = 100
    WFM_COSINE = 101
    WFM_SQUARE = 102
    WFM_SAWTOOTH = 103

    def __init__(self, freq, amplitude, waveformType=WFM_SINE):
        super().__init__()
        self.freq = freq
        self.amplitude = amplitude
        self.waveformType = waveformType

##### Arbitrary Command #####
# These commands should be used only when absolutely necessary as this breaks some of modularity paradigms in DataStation
# Additional command types can/will be added to address unforseen usecases.
# If you must use an arbitrary command, you need to register the arbitrary command in both the source as well as the hardware_object
# for them to work correctly.

class ArbitraryCommand(Command):
    def __init__(self, commandType, commandData):
        super().__init__()
        self.commandType = commandType
        self.commandData = commandData
