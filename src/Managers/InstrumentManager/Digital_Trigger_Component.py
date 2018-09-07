# -*- coding: utf-8 -*-
from Managers.InstrumentManager.Component import Component
import os, uuid

class Digital_Trigger_Component(Component):
    componentType = 'Digital Trigger Component'
    componentIdentifier = 'DigiTrigComp_mrb'
    componentVersion = '1.0'
    componentCreator = 'Matthew R. Brantley'
    componentVersionDate = '7/13/2018'
    iconGraphicSrc = 'Penning_Trap.png' #Not adjustable like layoutGraphicSrc
    valid = True
    isTriggerComponent = True

    def onCreation(self):
        self.compSettings['name'] = ''
        self.compSettings['layoutGraphicSrc'] = self.iconGraphicSrc
        self.compSettings['showSequencer'] = False
        self.compSettings['uuid'] = str(uuid.uuid4())
        self.compSettings['triggerComp'] = True

    def onRun(self):
        return True