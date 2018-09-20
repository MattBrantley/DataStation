from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os, sys, imp, math, uuid
from decimal import Decimal
from src.Constants import DSConstants as DSConstants, readyCheckPacket
from src.Managers.HardwareManager.Sources import Source

class eventType():
    name = 'Default Event'
    def __init__(self):
        self.time = 0
        self.eventParams = dict()

############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################

    def Get_Parameters(self):
        return self.eventParams

    def Add_Parameter(self, param):
        self.eventParams[param.name] = param

############################################################################################
###################################### OVERRIDE THESE ######################################

    def getLength(self, params):
        return 0

############################################################################################
#################################### INTERNAL USER ONLY ####################################

    def savePacket(self):
        savePacket = dict()
        savePacket['time'] = self.time
        savePacket['type'] = self.name
        paramDict = dict()
        for key, param in self.eventParams.items():
            paramDict[key] = param.value()
        savePacket['params'] = paramDict
        return savePacket

    def loadPacket(self, packet):
        self.time = packet['time']
        self.name = packet['type']
        for key, val in packet['params'].items():
            self.eventParams[key].setValue(val)

    def loadPacketParam(self, paramPacket):
        for key, val in paramPacket:
            pass

##### Parameters #####

class eventParameter():
    def __init__(self):
        self.name = ''
        self.paramValue = None
        self.paramSettings = dict() 
        self.paramSettings['value'] = None

    def value(self):
        return self.paramSettings['value']

    def v(self):
        return self.value()

    def setValue(self, value):
        self.paramSettings['value'] = value
        
class eventParameterDouble(eventParameter):
    def __init__(self, name, defaultVal=0, decimalPlaces=4, allowZero=True, allowNegative=True):
        super().__init__()
        self.name = name
        self.paramSettings['defaultVal'] = defaultVal
        self.paramSettings['decimalPlaces'] = decimalPlaces
        self.paramSettings['allowZero'] = allowZero
        self.paramSettings['allowNegative'] = allowNegative

class eventParameterInt(eventParameter):
    def __init__(self, name, defaultVal=0, allowZero=True, allowNegative=True):
        super().__init__()
        self.name = name
        self.paramSettings['defaultVal'] = defaultVal
        self.paramSettings['allowZero'] = allowZero
        self.paramSettings['allowNegative'] = allowNegative

class eventParameterString(eventParameter):
    def __init__(self, name):
        super().__init__()
        self.name = name
