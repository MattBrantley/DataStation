from Managers.InstrumentManager.Component import Component
import os, uuid

class Excitation_Plates(Component):
    componentType = 'Excitation Plates'
    componentIdentifier = 'excPlates_mrb'
    componentVersion = '1.0'
    componentCreator = 'Matthew R. Brantley'
    componentVersionDate = '7/26/2018'
    iconGraphicSrc = 'Excitation_Plates.png'
    valid = True
    def onCreation(self):
        self.compSettings['name'] = ''
        self.compSettings['layoutGraphicSrc'] = self.iconGraphicSrc
        self.compSettings['showSequencer'] = False
        self.compSettings['uuid'] = str(uuid.uuid4())

    def onRun(self):
        return True