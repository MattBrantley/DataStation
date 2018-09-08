from Managers.InstrumentManager.Component import *
from copy import deepcopy
from DSWidgets.controlWidget import readyCheckPacket

class Instrument(QObject):
    Instrument_Modified = pyqtSignal(object)
    Component_Modified = pyqtSignal(object)
    Events_Modified = pyqtSignal(object)

    name = ''

    def __init__(self, instrumentManager):
        super().__init__()
        self.instrumentManager = instrumentManager
        self.mW = self.instrumentManager.mW
        self.name = "Default Instrument"
        self.url = None
        self.components = list()
        self.fullSocketList = list()

    def checkTriggerComponents(self):
        removeList = list()

        for component in self.components:
            if(component.isTriggerComponent is True):
                obj = self.instrumentManager.getHardwareObjectByUUID(component.compSettings['hardwareObjectUUID'])
                if(obj is None):
                    removeList.append(component)

        for component in removeList:
            self.removeComponent(component)
                
    def readyCheck(self):
        subs = list()
        if(len(self.components) == 0):
            return readyCheckPacket('Active Instrument', DSConstants.READY_CHECK_ERROR, msg='Instrument has no components!')
        for component in self.components:
            subs.append(component.readyCheck())

        return readyCheckPacket('Active Instrument', DSConstants.READY_CHECK_READY, subs=subs)

    def addComponent(self, comp):
        newComp = type(comp)(self.mW)
        newComp.Component_Modified.connect(self.Component_Modified)
        newComp.Events_Modified.connect(self.Events_Modified)
        newComp.instrumentManager = self.instrumentManager
        newComp.setupWidgets()
        newComp.name = 'Unnamed Component'
        newComp.onCreationParent()
        newComp.onCreationFinishedParent()
        self.components.append(newComp)
        print('Instrument_Modified.emit()')
        self.Instrument_Modified.emit(self)
        return newComp

    def getComponentByUUID(self, uuid):
        for comp in self.components:
            if('uuid' in comp.compSettings):
                if(comp.compSettings['uuid'] == uuid):
                    return comp
        return None

    def getTrigCompsRefUUID(self, uuid):
        for comp in self.components:
            if('uuid' in comp.compSettings and comp.isTriggerComponent is True):
                print('Checking - ' + comp.compSettings['uuid'] + ':' + uuid)
                if(comp.compSettings['hardwareObjectUUID'] == uuid):
                    return comp
        return None

    def removeComponent(self, comp):
        comp.onRemovalParent()
        self.components.remove(comp)
        self.instrumentManager.mW.sequencerDockWidget.updatePlotList()
        self.instrumentManager.mW.hardwareWidget.drawScene()
        print('Instrument_Modified.emit()')
        self.Instrument_Modified.emit(self)

    def getSockets(self):
        self.fullSocketList.clear()
        for component in self.components:
            for socket in component.socketList:
                self.fullSocketList.append(socket)

        return self.fullSocketList

    def getSocketsByType(self, typeText):
        typeOut = type(None)
        if(typeText == 'Sockets: Analog Output'):
            typeOut = AOSocket
        elif(typeText == 'Sockets: Analog Input'):
            typeOut = AISocket
        elif(typeText == 'Sockets: Digital Output'):
            typeOut = DOSocket
        elif(typeText == 'Sockets: Digital Input'):
            typeOut = DISocket

        self.getSockets()
        self.outList = list()

        for socket in self.fullSocketList:
            if(isinstance(socket, typeOut) or typeText == 'All'):
                self.outList.append(socket)
        return self.outList

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