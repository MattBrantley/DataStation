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
        return True

    def Get_Path(self):
        return self.url

    def Set_Path(self, path):
        self.url = path
        return True

    def Get_Sockets(self, uuid=-1, inputUUID=-1, pathNo=-1, socketType=None):
        return self.getSockets(uuid, inputUUID, pathNo, socketType)

    def Get_Components(self):
        return self.componentList

    def Remove_Component(self, component):
        return self.removeComponent(component)

    def Add_Component(self, compModel, loadData=None):
        return self.addComponent(compModel, loadData)

    def Load_Sequence(self, path, showWarning=True):
        return self.loadSequence(path, showWarning)

    def Save_Sequence(self, name=None, path=None):
        pass

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
            self.componentList.remove(comp)
            self.iM.componentRemoved(self, comp)

    def reattachSockets(self):
        pass
    
    def clearEvents(self):
        for comp in self.componentList:
            comp.clearEvents()
        
##### Search Functions #####

    def getComponentByUUID(self, uuid):
        for comp in self.componentList:
            if('uuid' in comp.compSettings):
                if(comp.compSettings['uuid'] == uuid):
                    return comp
        return None

    def getComponents(self, uuid=-1):
        outList = list()
        for component in self.componentList:
            if(component.compSettings['uuid'] != uuid and uuid != -1):
                continue
            outList.append(component)
        return outList

    def getSockets(self, uuid=-1, inputUUID=-1, pathNo=-1, socketType=None):
        outList = list()
        for socket in self.getAllSockets():
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
        
    def getAllSockets(self):
        socketList = list()
        for component in self.componentList:
            socketList += component.Get_Sockets()
        return socketList

##### Event Functions #####

    def clearEvents(self):
        pass

    def loadSequence(self, path, showWarning=True):
        data = self.iM.openSequenceFile(self, path)
        self.mW.postLog('Applying sequence to instrument... ', DSConstants.LOG_PRIORITY_HIGH)

        if(data is None):
            self.mW.postLog('Sequence data was empty - aborting!', DSConstants.LOG_PRIORITY_HIGH)
            return False

        if(data['instrument'] != self.Get_Name() and showWarning is True):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("The sequence is for a different instrument (" + data['instrument'] + ") than what is currently loaded (" + self.Get_Name() + "). It is unlikely this sequence will load.. Continue?")
            msg.setWindowTitle("Sequence/Instrument Compatibability Warning")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

            retval = msg.exec_()
            if(retval == QMessageBox.No):
                return False

        self.clearEvents()

        for datum in data['saveData']:
            comp = self.getComponent(uuid=datum['uuid'])
            if(not comp):
                self.mW.postLog('Sequence data for comp with uuid (' + datum['uuid'] + ') cannot be assigned! Possibly from different instrument.', DSConstants.LOG_PRIORITY_HIGH)
            else:
                comp[0].loadSequenceData(datum['events'])

        self.mW.postLog('Sequence applied to instrument!', DSConstants.LOG_PRIORITY_HIGH)
        return True