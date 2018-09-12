from Managers.InstrumentManager.Component import *
from copy import deepcopy
from DSWidgets.controlWidget import readyCheckPacket

class Instrument(QObject):

    def __init__(self, iM):
        super().__init__()
        self.iM = iM
        self.mW = self.iM.mW
        self.name = "Default Instrument"
        self.url = None
        self.components = list()
        self.fullSocketList = list()

##### DataStation Interface Functions #####

    def readyCheck(self):
        subs = list()
        if(len(self.components) == 0):
            return readyCheckPacket('Active Instrument', DSConstants.READY_CHECK_ERROR, msg='Instrument has no components!')
        for component in self.components:
            subs.append(component.readyCheck())

        return readyCheckPacket('Active Instrument', DSConstants.READY_CHECK_READY, subs=subs)

##### Functions Called By Factoried Components #####

    def componentModified(self, component):
        pass

    def eventsModified(self, component):
        pass

    def socketAttached(self, component, socket):
        self.iM.socketAttached(self, component, socket)

    def socketDetatched(self, component, socket):
        self.iM.socketDetatched(self, component, socket)

##### Instrument Manipulations #####

    def saveInstrument(self):
        saveData = dict()
        saveData['name'] = self.name
        saveCompList = list()
        for component in self.components:
            saveCompList.append(component.onSaveParent())
        saveData['compList'] = saveCompList

        return saveData

    def loadPacket(self):
        pass
        #make all components and filters
        #then call restoreState on each - AFTER creating everything

##### Component Manipulations #####

    def checkTriggerComponents(self):
        removeList = list()

        for component in self.components:
            if(component.isTriggerComponent is True):
                obj = self.iM.getHardwareObjectByUUID(component.compSettings['hardwareObjectUUID'])
                if(obj is None):
                    removeList.append(component)

        for component in removeList:
            self.removeComponent(component)

    def addComponent(self, compModel):
        newComp = type(compModel)(self.mW)
        self.iM.componentModified(self)
        newComp.instr = self
        newComp.iM = self.iM
        newComp.mW = self.mW
        newComp.setupWidgets()
        newComp.name = 'Unnamed Component'
        newComp.onCreationParent()
        newComp.onCreationFinishedParent()
        self.components.append(newComp)
        self.iM.instrumentModified(self)
        return newComp

    def removeComponent(self, comp):
        if(comp is not None):
            comp.onRemovalParent()
            self.components.remove(comp)
            self.iM.mW.sequencerDockWidget.updatePlotList()
            self.iM.mW.hardwareWidget.drawScene()
            self.iM.instrumentModified(self)

    def reattachSockets(self):
        print('reattach')
    
    def clearSequenceEvents(self):
        for comp in self.components:
            comp.clearEvents()
        
##### Search Functions #####

    def getComponentByUUID(self, uuid):
        for comp in self.components:
            if('uuid' in comp.compSettings):
                if(comp.compSettings['uuid'] == uuid):
                    return comp
        return None

    def getTrigCompsRefUUID(self, uuid):
        for comp in self.components:
            if('uuid' in comp.compSettings and comp.isTriggerComponent is True):
                if(comp.compSettings['hardwareObjectUUID'] == uuid):
                    return comp
        return None
            
    def getSockets(self):
        self.fullSocketList.clear()
        for component in self.components:
            for socket in component.socketList:
                self.fullSocketList.append(socket)

        return self.fullSocketList

    def getSocketByUUID(self, uuid):
        socketList = self.getSockets()
        for socket in socketList:
            if(socket.socketSettings['uuid'] == uuid):
                return socket
        return None

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

#####