from src.Managers.InstrumentManager.Component import *
from src.Constants import readyCheckPacket
from copy import deepcopy

class Instrument(QObject):

    def __init__(self, iM):
        super().__init__()
        self.iM = iM
        self.mW = self.iM.mW
        self.name = 'Default Instrument'
        self.url = None
        self.componentList = list()

############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################

    def Get_Name(self):
        return self.name

    def Set_Name(self, name):
        self.name = name
        self.iM.instrumentConfigModified(self)

    def Get_Path(self):
        return self.url

    def Set_Path(self, path):
        self.url = path

    def Get_Sockets(self, uuid=-1, inputUUID=-1, pathNo=-1, socketType=None):
        return self.getSockets(uuid, inputUUID, pathNo, socketType)

    def Get_Components(self):
        return self.componentList

    def Add_Component(self, compModel, loadData=None):
        return self.addComponent(compModel, loadData)

############################################################################################
#################################### INTERNAL USER ONLY ####################################

##### DataStation Interface Functions #####

    def readyCheck(self):
        subs = list()
        if(len(self.componentList) == 0):
            return readyCheckPacket('Active Instrument', DSConstants.READY_CHECK_ERROR, msg='Instrument has no components!')
        for component in self.componentList:
            subs.append(component.readyCheck())

        return readyCheckPacket('Active Instrument', DSConstants.READY_CHECK_READY, subs=subs)

##### Functions Called By Factoried Components #####

    def eventAdded(self, component, event):
        self.iM.eventAdded(self, component, event)

    def eventRemoved(self, component, event):
        self.iM.eventRemoved(self, component, event)

    def eventModified(self, component, event):
        self.iM.eventModified(self, component, event)

    def socketAdded(self, component, socket):
        self.iM.socketAdded(self, component, socket)

    def socketAttached(self, component, socket):
        self.iM.socketAttached(self, component, socket)

    def socketDetatched(self, component, socket):
        self.iM.socketDetatched(self, component, socket)

##### Instrument Manipulations #####

    def savePacket(self):
        saveData = dict()
        saveData['name'] = self.name
        saveCompList = list()
        for component in self.componentList:
            saveCompList.append(component.onSaveParent())
        saveData['compList'] = saveCompList

        return saveData

    def loadPacket(self):
        pass

##### Component Manipulations #####

    def addComponent(self, compModel, loadData=None):
        newComp = type(compModel)(self.mW)
        self.iM.componentModified(self)
        newComp.instr = self
        newComp.iM = self.iM
        newComp.mW = self.mW
        newComp.setupWidgets()
        newComp.name = 'Unnamed Component'
        newComp.loadCompSettings(loadData)
        newComp.onCreationParent()
        newComp.onCreationFinishedParent()
        self.componentList.append(newComp)
        self.iM.componentAdded(self, newComp)
        return newComp

    def removeComponent(self, comp):
        if(comp is not None):
            comp.onRemovalParent()
            self.components.remove(comp)
            self.iM.componentRemoved(self, comp)

    def reattachSockets(self):
        pass
    
    def clearEvents(self):
        for comp in self.componentList:
            comp.clearEvents()
        
##### Search Functions #####

    def getComponentByUUID(self, uuid):
        for comp in self.components:
            if('uuid' in comp.compSettings):
                if(comp.compSettings['uuid'] == uuid):
                    return comp
        return None

    def getSockets(self, uuid=-1, inputUUID=-1, pathNo=-1, socketType=None):
        outList = list()
        for socket in self.getSocketObjs():
            if(socket.socketSettings['uuid'] != uuid and uuid != -1):
                continue
            if(socket.socketSettings['inputSource'] != inputUUID and inputUUID != -1):
                continue
            if(socket.socketSettings['inputSourcePathNo'] != pathNo and pathNo != -1):
                continue
            if(socketType is not None):
                if(isinstance(socket, socketType) is False):
                    continue
            outList.append(socket)
        return outList
        
    def getSocketObjs(self):
        socketList = list()
        for component in self.componentList:
            socketList += component.Get_Sockets()

        return socketList
#####