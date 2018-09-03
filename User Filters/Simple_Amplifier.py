# -*- coding: utf-8 -*-
"""
A simple DC Amplifier.
"""
from Managers.InstrumentManager.Filter import Filter
from Managers.InstrumentManager.Sockets import *
from PyQt5.Qt import *
from PyQt5.QtGui import *
import numpy as np
import os

class User_Filter(Filter):
    filterType = 'Simple Amplifier'
    filterIdentifier = 'SimpAmp_MRB'
    filterVersion = '1.0'
    filterCreator = 'Matthew R. Brantley'
    filterVersionDate = '8/13/2018'
    iconGraphicSrc = 'default.png'
    numPaths = 1
    valid = False

    def onCreation(self):
        self.filterSettings['name'] = 'Unnamed ' + self.filterType
        self.filterSettings['gain'] = 1
        self.filterSettings['offset'] = 0
        self.checkValidity()

    def checkValidity(self):
        self.valid = True

    def procForward(self, inputs):
        return None

    def procReverse(self, pathNo, packetIn, packetType):
        if(self.isDCWaveformPacket(packetIn)):
            ampedValues = packetIn.waveformData
            ampedValues[:,1] = packetIn.waveformData[:,1] * self.filterSettings['gain']
            packetOut = DCWaveformPacket(ampedValues)
            return packetOut
        
        return None