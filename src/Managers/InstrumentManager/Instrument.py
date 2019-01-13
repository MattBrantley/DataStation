from src.Managers.InstrumentManager.Component import *
from src.Managers.InstrumentManager.EventSequence import EventSequence
from copy import deepcopy
import json, os

class Instrument(QObject):
############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################

    def Get_Name(self):
        return self.name

    def Set_Name(self, name):
        self.name = name
        self.iM.instrumentNameChanged(self)
        return True

    def Set_UUID(self, uuid):
        self.uuid = uuid
        self.iM.instrumentUUIDChanged(self)
        return True

    def Get_Path(self):
        return self.getPath()

    def Set_Path(self, path):
        self.url = path
        return True

    def Get_UUID(self):
        return self.uuid

    def Get_Sockets(self, uuid=-1, inputUUID=-1, pathNo=-1, socketType=None):
        return self.getSockets(uuid, inputUUID, pathNo, socketType)

    def Get_Components(self, uuid=-1):
        return self.getComponents(uuid)

    def Remove_Component(self, component):
        return self.removeComponent(component)

    def Add_Component(self, compModel, customFields=dict(), loadData=None):
        # customFields is a dictionary containing any customFields that should be applied before the component_add is emitted.
        return self.addComponent(compModel, customFields, loadData)

    def Get_Sequence(self):
        return self.sequence

    def Load_Sequence(self, path):
        self.Get_Sequence().Load_Sequence_File(path)

    def Save_Sequence(self, filepath):
        self.Get_Sequence().Save_Sequence(filepath)

    def Save_Instrument(self, name=None, path=None):
        if(name is not None):
            self.Set_Name(name)
        if(path is not None):
            self.Set_Path(path)
        self.saveInstrument()

    def Load_Instrument_File(self, path):
        self.loadInstrumentFile(path)

    def Get_Sequence_Directory(self):
        return os.path.join(self.iM.Sequences_Save_Directory(), self.Get_Name())

    def Ready_Check(self):
        self.readyCheck()

    def Ready_Check_Status(self):
        if not self.readyCheckList:
            return True
        else:
            return False

    def Ready_Check_List(self):
        return self.readyCheckList

    def Fail_Ready_Check(self, trace, msg, warningLevel=DSConstants.READY_CHECK_ERROR):
        self.readyCheckFail(trace, msg, warningLevel)

    def Get_Hardware_Devices(self):
        return self.getHardwareDevices()

    def Run_Instrument(self):
        self.runInstrument()

    def Get_Run_ID(self):
        return self.runID

############################################################################################
#################################### INTERNAL USER ONLY ####################################
    def __init__(self, ds):
        super().__init__()
        self.ds = ds
        self.iM = ds.iM
        self.name = 'Default Instrument'
        self.readyCheckList = list()
        self.directory = None
        self.sequence = EventSequence(self.ds, self)
        self.componentList = list()
        self.uuid = str(uuid.uuid4())
        self.runID = ''

##### Instrument Ready Check #####
    def readyCheck(self):
        if self.ds.Is_Loaded() is True:
            self.readyCheckList = list()
            trace = list()
            trace.append(self)
            if(self.Get_Components() == []):
                trace[0].Fail_Ready_Check(trace, 'Instrument Has No Components!')
            for comp in self.componentList:
                comp.readyCheck(trace)
            self.sequence.readyCheck(trace)
        else:
            self.ds.postLog('Cannot Ready Check Instrument (' + self.name + ') While DataStation is Loading ', DSConstants.LOG_PRIORITY_HIGH)


    def readyCheckFail(self, trace, msg, warningLevel):
        self.readyCheckList.append({'Trace': trace, 'Msg': msg, 'Level': warningLevel})

##### Functions Called By Factoried Components #####
    ##### Component #####
    def componentReadyCheckInterrupt(self, component, socket, msg):
        readyCheckMsg = dict()
        readyCheckMsg['Trace']  = [component, socket, msg]
        readyCheckMsg['msg'] = msg
        self.readyCheckFails.append(readyCheckMsg)
        self.ready = False

    def componentStandardFieldChanged(self, component, field):
        self.iM.componentStandardFieldChanged(self, component, field)

    def componentCustomFieldChanged(self, component, field):
        self.iM.componentCustomFieldChanged(self, component, field)

    ##### Socket #####
    def socketAdded(self, component, socket):
        self.iM.socketAdded(self, component, socket)

    def socketAttached(self, component, socket):
        self.iM.socketAttached(self, component, socket)

    def socketDetatched(self, component, socket):
        self.iM.socketDetatched(self, component, socket)

    ##### Event #####
    def eventAdded(self, component, event):
        self.iM.eventAdded(self, component, event)

    def eventRemoved(self, component, event):
        self.iM.eventRemoved(self, component, event)

    def eventModified(self, component, event):
        self.iM.eventModified(self, component, event)

    ##### Component Programming #####
    def programmingModified(self, component):
        self.iM.programmingModified(self, component)

    def measurementRecieved(self, component, socket, measurementPacket):
        self.iM.measurementRecieved(self, component, socket, measurementPacket)

##### Functions Called By Sequence #####
    def sequenceSaved(self):
        self.iM.sequenceSaved(self)

    def sequenceLoaded(self):
        self.iM.sequenceLoaded(self)

##### Hardware Manipulations ####
    def runInstrument(self):
        self.generateNewRunID()

        for handler in self.Get_Hardware_Devices():
            handler.onRun()
        self.iM.instrumentSequenceRunning(self)

    def generateNewRunID(self):
        self.runID = str(uuid.uuid4())

    def getHardwareDevices(self):
        hardwareHandlerList = list()
        for component in self.Get_Components():
            for socket in component.Get_Sockets():
                source = socket.Get_Source()
                if source is not None:
                    hardwareHandlerList.append(source.Get_Handler())

        hardwareHandlerSet = set(hardwareHandlerList)
        return list(hardwareHandlerSet)

##### Instrument Manipulations #####
    def savePacket(self):
        saveData = dict()
        saveData['name'] = self.Get_Name()
        saveData['UUID'] = self.Get_UUID()
        saveCompList = list()
        for component in self.componentList:
            saveCompList.append(component.onSaveParent())
        saveData['compList'] = saveCompList

        return saveData

    def loadPacket(self):
        pass

    def getPath(self):
        if(self.directory is None):
            instrumentSaveURL = self.iM.Instrument_Save_Directory()  
        else:
            instrumentSaveURL = self.directory

        return os.path.join(instrumentSaveURL, self.Get_Name() + '.dsinstrument') 

    #### Save Instrument ####
    def saveInstrument(self):
        self.ds.postLog('VI_Save', DSConstants.LOG_PRIORITY_HIGH, textKey=True)
        self.iM.instrumentSaving(self)
        self.writeInstrumentToFile()
        self.iM.instrumentSaved(self)
        self.ds.postLog(' ...Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)

    def writeInstrumentToFile(self): ### Implement swap ASAP
        fullPath = self.Get_Path()

        if(os.path.exists(fullPath)):
            os.remove(fullPath)
        with open(fullPath, 'w') as file:
            json.dump(self.savePacket(), file, sort_keys=True, indent=4)

    #### Load Instrument ####
    def loadInstrumentFile(self, path):
        self.directory = os.path.dirname(path)
        self.ds.postLog('Loading User Instrument (' + path + ')... ', DSConstants.LOG_PRIORITY_HIGH)
        if(os.path.exists(path) is False):
            self.ds.postLog('Path (' + path + ') does not exist! Aborting! ', DSConstants.LOG_PRIORITY_HIGH)
            return

        with open(path, 'r') as file:
            try:
                instrumentData = json.load(file)
                if(isinstance(instrumentData, dict)):
                    self.processInstrumentData(instrumentData)
            except ValueError as e:
                self.ds.postLog('Corrupted instrument at (' + path + ') - aborting! ', DSConstants.LOG_PRIORITY_MED)

    def processInstrumentData(self, instrumentData):
        if('name' in instrumentData):
            self.Set_Name(instrumentData['name'])
        if('UUID' in instrumentData):
            self.Set_UUID(instrumentData['UUID'])
        else:
            return False

        if('compList' in instrumentData):
            for comp in instrumentData['compList']:
                if(('compIdentifier' in comp) and ('compType' in comp)):
                    compModel = self.iM.findCompModelByIdentifier(comp['compIdentifier'])
                    if(compModel is None):
                        self.ds.postLog('Instrument contains component (' + comp['compType'] + ':' + comp['compIdentifier'] + ') that is not in the available component modules. Ignoring this component!', DSConstants.LOG_PRIORITY_MED)
                    else:
                        result = self.Add_Component(compModel, loadData=comp['compSettings'])
                        if('sockets' in comp):
                            if(isinstance(comp['sockets'], list)):
                                result.loadSockets(comp['sockets'])

        self.iM.instrumentLoaded(self)
        return True

##### Component Manipulations #####
    def addComponent(self, compModel, customFields=dict(), loadData=None):
        newComp = type(compModel)(self.ds)
        newComp.instr = self
        newComp.iM = self.iM
        newComp.ds = self.ds
        #newComp.name = 'Unnamed Component'
        newComp.loadCustomFields(customFields)
        newComp.loadCompSettings(loadData)
        newComp.onCreationParent()
        newComp.onCreationFinishedParent()
        self.componentList.append(newComp)
        self.iM.componentAdded(self, newComp)
        self.ds.postLog('Added New Component to Instrument: ' + newComp.componentType, DSConstants.LOG_PRIORITY_MED)
        return newComp

    def removeComponent(self, comp):
        if(comp is not None):
            comp.onRemovalParent()
            self.componentList.remove(comp)
            self.iM.componentRemoved(self, comp)

##### Search Functions #####

    def getComponents(self, uuid):
        outList = list()
        for component in self.componentList:
            if(component.compSettings['uuid'] != uuid and uuid != -1):
                continue
            outList.append(component)
        return outList

    def getSockets(self, uuid, inputUUID, pathNo, socketType):
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

