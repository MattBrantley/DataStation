# -*- coding: utf-8 -*-

from src.Managers.HardwareManager.Filter import *
from src.Managers.InstrumentManager.Sockets import *
from PyQt5.Qt import *
from PyQt5.QtGui import *
import numpy as np
import os

class User_Filter(AnalogFilter):
    filterType = '275i Log-Linear Output'
    filterIdentifier = '275iLL_MRB'
    filterVersion = '1.0'
    filterCreator = 'Matthew R. Brantley'
    filterVersionDate = '6/26/2019'
    iconGraphicSrc = 'default.png'
    numPaths = 1

    valid = False

    def onCreation(self):
        self.filterSettings['name'] = 'Unnamed ' + self.filterType
        self.checkValidity()

    def checkValidity(self):
        self.valid = True

    def procForward(self, programmingPacket):
        return programmingPacket

    def procReverse(self, measurementPacket):
        #print('275i---------------------------------------------')
        #print(measurementPacket.getMeasurements()[0].yData())

        measurementPacket.getMeasurements()[0].wave = np.power(10, measurementPacket.getMeasurements()[0].wave - 5)
        
        #print(measurementPacket.getMeasurements()[0].yData())
        return measurementPacket