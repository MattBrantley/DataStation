# -*- coding: utf-8 -*-
"""
Splits an incoming signal to three outputs
"""
from Managers.InstrumentManager.Filter import *
from PyQt5.Qt import *
from PyQt5.QtGui import *
import os

class User_Filter(AnalogFilter):
    filterType = 'Signal Splitter 3-Way'
    filterIdentifier = 'SigSplit3_MRB'
    filterVersion = '1.0'
    filterCreator = 'Matthew R. Brantley'
    filterVersionDate = '8/13/2018'
    iconGraphicSrc = 'default.png'
    numPaths = 3
    valid = False

    def onCreation(self):
        self.filterSettings['name'] = 'Unnamed ' + self.filterType
        self.checkValidity()

    def checkValidity(self):
        self.valid = True

    def procForward(self, dataIn):
        pass