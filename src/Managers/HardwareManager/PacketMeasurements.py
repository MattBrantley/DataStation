import numpy as np

class measurementPacket():
############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################
    def Add_Measurement(self, measurement):
        self.measurementList.append(measurement)

    def Remove_Measurement(self, measurement):
        self.measurementList.remove(measurement)

    #def Set_Origin_Socket(self, socket):
    #    self.originSocket = socket

    def Get_Measurements(self, measurementType=None):
        return self.getMeasurements(measurementType)

############################################################################################
#################################### INTERNAL USER ONLY ####################################
    def __init__(self):
        self.measurementList = list()
        #self.originSocket = None

    def getMeasurements(self, measurementType=None):
        outList = list()
        for measurement in self.measurementList:
            if(measurementType is not None):
                if(issubclass(measurementType, type(measurement)) is False):
                    continue

            outList.append(measurement)
        return outList

class Measurement():
    def __init__(self):
        pass

##### Digital Measurements #####

#class DigitalWaveformCommand(Command):
#    def __init__(self, rate, yData):
#        super().__init__()
#        self.rate = rate
#        self.yData = yData

#class DigitalSparseCommand(Command):
#    def __init__(self, pairs):
#        super().__init__()
#        self.pairs = pairs

##### Analog Measurements #####

class AnalogWaveformMeasurement(Measurement):
    def __init__(self, t0, f, wave):
        super().__init__()
        self.t0 = t0
        self.f = f # is in units of Hertz (Hz)
        self.wave = wave # is in units of voltage (V)

    def toPairs(self):
        len = self.wave.shape[0]/self.f
        x = np.arange(self.t0, self.t0 + len, 1/self.f)
        y = self.wave
        res = np.vstack([x, y]).transpose()
        return res

#class AnalogSparseCommand(Command):
#    def __init__(self, pairs):
#        self.pairs = pairs # numpy array: column 1 = time (second), column 2 = voltage (V)