# -*- coding: utf-8 -*-
"""
A quadrupole ion guide
"""
from Component import Component
import os

class User_Component(Component):
    componentType = 'Quadrupole'
    componentVersion = '1.0'
    componentCreator = 'Matthew R. Brantley'
    componentVersionDate = '7/26/2018'
    iconGraphicSrc = 'Quad_Short.png'

    def onCreation(self):
        self.compSettings['name'] = ''
        self.compSettings['layoutGraphicSrc'] = self.iconGraphicSrc

    def onRun(self):
        return True