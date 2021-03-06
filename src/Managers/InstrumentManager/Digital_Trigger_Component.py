# -*- coding: utf-8 -*-
from src.Managers.InstrumentManager.Component import *
from src.Managers.InstrumentManager.Sockets import *
import os, uuid, numpy as np

class Digital_Trigger_Component(Component):
    componentType = 'Digital Trigger Component'
    componentIdentifier = 'DigiTrigComp_mrb'
    componentVersion = '1.0'
    componentCreator = 'Matthew R. Brantley'
    componentVersionDate = '7/13/2018'
    iconGraphicSrc = 'default.png' #Not adjustable like layoutGraphicSrc
    valid = True
    isTriggerComponent = True

    def onCreation(self):
        self.compSettings['name'] = 'Digital Trigger'
        self.compSettings['layoutGraphicSrc'] = self.iconGraphicSrc
        self.compSettings['showSequencer'] = False
        self.compSettings['uuid'] = str(uuid.uuid4())
        self.compSettings['triggerComp'] = True
        self.compSettings['hardwareObjectUUID'] = ''

    def onConnect(self, name, hardwareObjectUUID):
        self.compSettings['hardwareObjectUUID'] = hardwareObjectUUID
        self.genTriggerSocket(name=name)

    def genTriggerSocket(self, name = ''):
        self.socket = self.addDISocket('[DIGI TRIG]: ' + name)

    def onRun(self, events):
        #Update self.data here
        dataPacket = waveformPacket(self.data)
        self.setPathDataPacket(1, dataPacket)
        return True
