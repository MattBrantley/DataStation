from src.Managers.InstrumentManager.Component import *
from src.Managers.InstrumentManager.EventSequence import EventSequence
from src.Managers.InstrumentManager.ReadyCheck import ReadyCheckList
from copy import deepcopy
import datetime, json, os

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
        self.readyCheck()

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
        return self.readyCheckStatus()

    def Ready_Check_List(self):
        return self.readyCheckList

    def Fail_Ready_Check(self, trace, msg, warningLevel=DSConstants.READY_CHECK_ERROR):
        self.readyCheckMessage(trace, msg, warningLevel)

    def Warning_Ready_Check(self, trace, msg, warningLevel=DSConstants.READY_CHECK_WARNING):
        self.readyCheckMessage(trace, msg, warningLevel)

    def Get_Hardware_Devices(self):
        return self.getHardwareDevices()

    def Run_Instrument(self):
        self.runInstrument()

    def Stop_Instrument(self):
        self.stopInstrument()

    def Reset_Instrument(self):
        self.resetInstrument()

    def Get_Run_ID(self):
        return self.runID

    def Can_Run(self):
        return self.canRun

    def Is_Running(self):
        return self.isRunning

    def Get_Run_Time(self):
        return self.getRunTime()

############################################################################################
#################################### INTERNAL USER ONLY ####################################
    def __init__(self, ds):
        super().__init__()
        self.ds = ds
        self.iM = ds.iM
        self.name = 'Default Instrument'
        self.canRun = False
        self.isStarting = False
        self.isRunning = False
        self.readyCheckList = ReadyCheckList()
        self.directory = None
        self.sequence = EventSequence(self.ds, self)
        self.componentList = list()
        self.trigComponentList = list()
        self.uuid = str(uuid.uuid4())
        self.runID = ''

        self.startReadyCheckTimer()

##### Instrument Ready Check #####
    def readyCheck(self):
        if self.ds.Is_Loaded() is True:
            self.readyCheckList = ReadyCheckList()
            trace = list()
            trace.append(self)
            if(self.Get_Components() == []):
                trace[0].Fail_Ready_Check(trace, 'Instrument Has No Components!')
            for comp in self.componentList:
                comp.readyCheck(trace)
            self.sequence.readyCheck(trace)

            self.canRun = self.readyCheckList.Can_Run()
            if self.canRun is False and self.isStarting is True:
                self.isStarting = False
                self.isRunning = True

            if self.canRun is True and self.isRunning is True:
                self.isRunning = False

            self.iM.instrumentReadyChecked(self)
        else:
            self.ds.postLog('Cannot Ready Check Instrument (' + self.name + ') While DataStation is Loading ', DSConstants.LOG_PRIORITY_HIGH)

    def readyCheckStatus(self):
        self.readyCheckList.Get_Status()

    def readyCheckMessage(self, trace, msg, warningLevel):
        self.readyCheckList.append({'Trace': trace, 'Msg': msg, 'Level': warningLevel})
        
    def startReadyCheckTimer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.readyCheck)
        self.timer.start(25)

##### Functions Called By Factoried Components #####
    ##### Component #####
    def componentReadyCheckInterrupt(self, component, socket, msg):
        readyCheckMsg = dict()
        readyCheckMsg['Trace']  = [component, socket, msg]
        readyCheckMsg['msg'] = msg
        self.ready = False
        self.readyCheck()

    def componentStandardFieldChanged(self, component, field):
        self.iM.componentStandardFieldChanged(self, component, field)
        self.readyCheck()

    def componentCustomFieldChanged(self, component, field):
        self.iM.componentCustomFieldChanged(self, component, field)
        self.readyCheck()

    ##### Socket #####
    def socketAdded(self, component, socket):
        self.iM.socketAdded(self, component, socket)
        self.readyCheck()

    def socketAttached(self, component, socket):
        self.iM.socketAttached(self, component, socket)
        self.readyCheck()

    def socketDetatched(self, component, socket):
        self.iM.socketDetatched(self, component, socket)
        self.readyCheck()

    ##### Event #####
    def eventsModified(self, component):
        self.iM.eventsModified(self, component)
        self.readyCheck()

    ##### Component Programming #####
    def programmingModified(self, component):
        self.iM.programmingModified(self, component)
        self.readyCheck()

    def measurementRecieved(self, component, socket, measurementPacket):
        self.iM.measurementRecieved(self, component, socket, measurementPacket)
        self.readyCheck()

##### Functions Called By Sequence #####
    def sequenceSaved(self):
        self.iM.sequenceSaved(self)
        self.readyCheck()

    def sequenceLoaded(self):
        self.iM.sequenceLoaded(self)

        for hardware in self.Get_Hardware_Devices():
            hardware.Disable_Programming_Lock()
            hardware.Push_Programming()

        self.readyCheck()

##### Hardware Manipulations ####
    def runTimeFraction(self):
        return self.Get_Run_Time() / self.Get_Sequence().Get_Sequence_Length()

    def runInstrument(self):
        if self.Can_Run():
            self.isStarting = True
            self.canRun = False
            self.generateNewRunID()

            self.checkProgramming()

            for handler in self.Get_Hardware_Devices():
                handler.onRun()

            self.iM.instrumentSequenceRunning(self)
        else:
            self.ds.postLog('Instrument (' + self.name + ') Run Request Denied - Failed Ready Check ', DSConstants.LOG_PRIORITY_HIGH)

    def stopInstrument(self): # Not really implemented yet..
        if self.Is_Running():
            for handler in self.Get_Hardware_Devices():
                handler.onStop()

    def resetInstrument(self):
        for component in self.Get_Components():
            component.Reset_Component()

        for hardware in self.Get_Hardware_Devices():
            hardware.Push_Programming()

    def generateNewRunID(self):
        self.runID = str(uuid.uuid4())
        self.runStart = datetime.datetime.now()

    def getRunTime(self):
        if self.isRunning:
            return (datetime.datetime.now() - self.runStart).total_seconds()
        else:
            return 0

    def checkProgramming(self):
        hardwareHandlerList = list()

        for component in self.Get_Components():
            for socket in component.Get_Sockets():
                if socket.Get_Source().Get_Programming_Instrument() is not self:
                    socket.Push_Programming()
                    source = socket.Get_Source()
                    if source is not None:
                        hardwareHandlerList.append(source.Get_Handler())

        for hardware in set(hardwareHandlerList):
            hardware.Push_Programming()

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
        self.readyCheck()

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

