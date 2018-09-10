# -*- coding: utf-8 -*-
"""
A quadrupole ion guide
"""
from Managers.InstrumentManager.Component import Component
import os, uuid

class Quadrupole(Component):
    componentType = 'Quadrupole'
    componentIdentifier = 'quad_mrb'
    componentVersion = '1.0'
    componentCreator = 'Matthew R. Brantley'
    componentVersionDate = '7/26/2018'
    iconGraphicSrc = 'Quad_Short.png'
    valid = True

    def onCreation(self):
        self.compSettings['name'] = ''
        self.compSettings['layoutGraphicSrc'] = self.iconGraphicSrc
        self.compSettings['showSequencer'] = False
        self.compSettings['uuid'] = str(uuid.uuid4())
        self.socket = self.addDISocket(self.compSettings['name'])

    def onRun(self):
        return True