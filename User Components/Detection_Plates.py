from Component import Component
import os, uuid

class Detection_Plates(Component):
    componentType = 'Detection Plates'
    componentIdentifier = 'detecPlates_mrb'
    componentVersion = '1.0'
    componentCreator = 'Matthew R. Brantley'
    componentVersionDate = '7/26/2018'
    iconGraphicSrc = 'Detection_Plates.png'
    valid = True
    
    def onCreation(self):
        self.compSettings['name'] = ''
        self.compSettings['layoutGraphicSrc'] = self.iconGraphicSrc
        self.compSettings['showSequencer'] = False
        self.compSettings['uuid'] = str(uuid.uuid4())

    def onRun(self):
        return True