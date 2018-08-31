from Component import *
from copy import deepcopy
from DSWidgets.controlWidget import readyCheckPacket

class Instrument():
    name = ''

    def __init__(self, instrumentManager):
        self.instrumentManager = instrumentManager
        self.name = "Default Instrument"
        self.url = None
        self.components = list()
        self.fullSocketList = list()

    def readyCheck(self):
        subs = list()
        if(len(self.components) == 0):
            return readyCheckPacket('Active Instrument', DSConstants.READY_CHECK_ERROR, msg='Instrument has no components!')
        for component in self.components:
            subs.append(component.readyCheck())

        return readyCheckPacket('Active Instrument', DSConstants.READY_CHECK_READY, subs=subs)

    def addComponent(self, comp):
        newComp = type(comp)(self)
        newComp.instrumentManager = self.instrumentManager
        newComp.setupWidgets()
        newComp.name = 'Unnamed Component'
        newComp.onCreationParent()
        newComp.onCreationFinishedParent()
        self.components.append(newComp)
        return newComp

    def getComponentByUUID(self, uuid):
        for comp in self.components:
            if('uuid' in comp.compSettings):
                if(comp.compSettings['uuid'] == uuid):
                    return comp
        return None

    def removeComponent(self, comp):
        comp.onRemovalParent()
        self.components.remove(comp)
        self.instrumentManager.mainWindow.sequencerDockWidget.updatePlotList()
        self.instrumentManager.mainWindow.hardwareWidget.drawScene()

    def getSockets(self):
        self.fullSocketList.clear()
        for component in self.components:
            for socket in component.socketList:
                self.fullSocketList.append(socket)

        return self.fullSocketList

    def saveInstrument(self):
        saveData = dict()
        saveData['name'] = self.name
        saveCompList = list()
        for component in self.components:
            saveCompList.append(component.onSaveParent())
        saveData['compList'] = saveCompList

        return saveData

    def reattachSockets(self):
        for socket in self.getSockets():
            socket.onLink()

    def clearSequenceEvents(self):
        for comp in self.components:
            comp.clearEvents()