# -*- coding: utf-8 -*-
"""
Splits an incoming signal to two outputs
"""
from Filter import Filter
from PyQt5.Qt import *
from PyQt5.QtGui import *
import os

class User_Filter(Filter):
    filterType = 'Signal Splitter 2-Way'
    filterIdentifier = 'SigSplit2_MRB'
    filterVersion = '1.0'
    filterCreator = 'Matthew R. Brantley'
    filterVersionDate = '8/13/2018'
    iconGraphicSrc = 'default.png'
    numPaths = 2
    valid = False

    def onCreation(self):
        self.filterSettings['name'] = 'Unnamed ' + self.filterType
        self.checkValidity()

    def checkValidity(self):
        self.valid = True

    def procForward(self, dataIn):
        pass