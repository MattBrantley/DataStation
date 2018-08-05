from Component import *
from copy import deepcopy

class Instrument():
    components = list()
    name = ''

    def __init__(self, instrumentManager):
        self.instrumentManager = instrumentManager
        self.name = "Default Instrument"

        #self.loadTestInstrument()
        #self.showInstruments()

    def addComponent(self, comp):
        newComp = type(comp)(self)
        newComp.instrumentManager = self.instrumentManager
        newComp.setupWidgets()
        newComp.name = 'Unnamed Component'
        newComp.onCreationParent()
        self.components.append(newComp)
        return newComp

    def showInstruments(self):
        for x in self.components:
            print(x.name)
            print(x.layoutGraphicSrc)