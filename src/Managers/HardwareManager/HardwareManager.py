import os, sys, imp
from src.Managers.InstrumentManager.Instrument import *
from src.Managers.InstrumentManager.Sockets import *
from src.Managers.InstrumentManager.Digital_Trigger_Component import Digital_Trigger_Component
from src.Managers.HardwareManager.HardwareDevice import HardwareDeviceHandler, HardwareDevice
from src.Managers.HardwareManager.Sources import *
from src.Managers.HardwareManager.Filter import *
from src.Managers.HardwareManager.DataStation_Labview import DataStation_LabviewExtension
from src.Constants import DSConstants as DSConstants, readyCheckPacket
import json as json

class HardwareManager(QObject):

############################################################################################
##################################### EXTERNAL SIGNALS #####################################

##### Signals: Hardware State #####
    Hardware_State_Loaded = pyqtSignal()
    Hardware_State_Saving = pyqtSignal()

##### Signals: Hardware #####
    Hardware_Handler_Soft_Trigger_Sent = pyqtSignal(object) # hardware

    Hardware_Scanned = pyqtSignal(object) # hardware
    Hardware_Initialized = pyqtSignal(object) # hardware
    Hardware_Configured = pyqtSignal(object) # hardware
    Hardware_Programmed = pyqtSignal(object) # hardware
    Hardware_Soft_Triggered = pyqtSignal(object) # hardware

    Hardware_Status_Message = pyqtSignal(object, str) # hardware, message
    Hardware_Ready_Status_Changed = pyqtSignal(object, bool) # hardware, readyStatus

    Hardware_Added = pyqtSignal(object) # hardware
    Hardware_Removed = pyqtSignal()
    Hardware_Trigger_Modified = pyqtSignal()
    Hardware_Programming_Modified = pyqtSignal(object, object) # hardware, source
    Hardware_Device_Reset = pyqtSignal(object) # hardware
    Hardware_Device_Changed = pyqtSignal(object, str) # hardware, device name
    Hardware_Device_Removed = pyqtSignal(object) # hardware
    Hardware_Device_Found = pyqtSignal(object, str) # hardware, device name

    Hardware_Device_Trigger_Mode_Added = pyqtSignal(object, str) # hardware, trigger name

##### Signals: Sequence #####
    Sequence_Started = pyqtSignal()
    Sequence_Finished = pyqtSignal()

##### Signals: Sources #####
    Source_Added = pyqtSignal(object, object) # hardware, source
    Source_Removed = pyqtSignal(object, object) # hardware, source

##### Signals: Filters #####
    Filter_Added = pyqtSignal(object) # Filter
    Filter_Attached = pyqtSignal(object) # Filter
    Filter_Detatched = pyqtSignal(object) # Filter
    Filter_Removed = pyqtSignal(object) # Filter

############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################

##### Functions: Instrument Manager #####
    def Do_Ready_Check(self):
        return self.readyCheck()

    def Ready_Check_Status(self):
        return self.readyStatus

    def Fail_Ready_Check(self, trace, msg):
        if(isinstance(trace[0], Instrument)):
            trace[0].Fail_Ready_Check(trace, msg)

##### Functions: Hardware Models #####

    def Get_Hardware_Models_Available(self):
        return self.driversAvailable

##### Functions: Filter Models #####

    def Get_Filter_Models_Available(self):
        return self.filtersAvailable

##### Functions: Hardware #####
    def Get_Hardware(self):
        return self.deviceHandlerList

    def Add_Hardware(self, hardwareModel):
        return self.addHardwareObj(hardwareModel)

    def Remove_Hardware(self, hardwareObject):
        return self.removeHardwareObj(hardwareObject)

    def Add_Filter(self, filterModel):
        return self.addFilter(filterModel)

    def Get_Filters(self, uuid=-1, inputUUID=-1, pathNo=-1, filterType=None):
        return self.getFilters(uuid, inputUUID, pathNo, filterType)

    def Get_Sources(self, uuid=-1, sourceType=None):
        return self.getSources(uuid, sourceType)

############################################################################################
#################################### INTERNAL USER ONLY ####################################
    def __init__(self, ds):
        super().__init__()

        self.ds = ds
        self.readyStatus = False
        self.filtersDir = os.path.join(self.ds.rootDir, 'Filters')
        self.hardwareDriverDir = os.path.join(self.ds.rootDir, 'Hardware Drivers')
        self.hardwareStatePath = os.path.join(self.ds.rootDir, 'HardwareState.json')

        self.filtersAvailable = list()
        self.driversAvailable = list()
        self.deviceHandlerList = list()
        self.sourceObjList = list()
        self.filterList = list()

        self.loadFilters()
        self.loadHardwareDrivers()
        self.loadLabviewInterface()

        self.ds.DataStation_Loaded.connect(self.loadHardwareState)
        self.ds.DataStation_Closing.connect(self.saveHardwareState)

    def connections(self):
        self.iM = self.ds.iM
        self.wM = self.ds.wM

##### DataStation Reserved Functions #####

    def readyCheck(self):
        subs = list()
        self.readyStatus = True
        for deviceHandler in self.deviceHandlerList:
            check = deviceHandler.readyCheck()
            subs.append(check)
            if(check.readyStatus is False):
                self.readyStatus = False

        return readyCheckPacket('Hardware Manager', DSConstants.READY_CHECK_READY, subs=subs)

##### Functions Called By Factoried Hardware Device Handlers #####
    def handlerSoftTriggerSent(self, hWare):
        self.Hardware_Handler_Soft_Trigger_Sent.emit(hWare)

    def hardwareScanned(self, hWare):
        self.Hardware_Scanned.emit(hWare)

    def hardwareInitialized(self, hWare):
        self.Hardware_Initialized.emit(hWare)

    def hardwareConfigured(self, hWare):
        self.Hardware_Configured.emit(hWare)

    def hardwareProgrammed(self, hWare):
        self.Hardware_Programmed.emit(hWare)

    def hardwareSoftTriggered(self, hWare):
        self.Hardware_Soft_Triggered.emit(hWare)

    def hardwareDeviceFound(self, hWare, deviceName):
        self.Hardware_Device_Found.emit(hWare, deviceName)

    def hardwareStatusMessage(self, hWare, msg):
        self.Hardware_Status_Message.emit(hWare, msg)

    def hardwareReadyStatusChanged(self, hWare, status):
        self.Hardware_Ready_Status_Changed.emit(hWare, status)

    def programmingModified(self, hWare, source):
        self.Hardware_Programming_Modified.emit(hWare,source)

    def deviceReset(self, hWare):
        self.Hardware_Device_Reset.emit(hWare)

    def triggerModified(self, hWare):
        pass

    def sourceAdded(self, hardwareObj, sourceObj): # Source_Added
        self.Source_Added.emit(hardwareObj, sourceObj)

    def triggerModeAdded(self, hardwareObj, triggerModeName): #Trigger_Mode_Name
        self.Hardware_Device_Trigger_Mode_Added.emit(hardwareObj, triggerModeName)

    def sourceRemoved(self, hardwareObj, sourceObj): # Source_Removed
        self.Source_Removed.emit(hardwareObj, sourceObj)

    def deviceSelectionChanged(self, hardwareObj, deviceName):
        self.Hardware_Device_Changed.emit(hardwareObj, deviceName)

    def deviceSelectionRemoved(self, hardwareObj):
        self.Hardware_Device_Removed.emit(hardwareObj)

##### Functions Called By Factoried Filter Objects #####

    def removeFilter(self, Filter): # Filter_Removed
        self.Filter_Removed.emit(Filter)
        self.filterList.remove(Filter)

    def filterAttached(self, Filter): # Filter_Attached
        self.Filter_Attached.emit(Filter)

    def filterDetatched(self, Filter): # Filter_Detatched
        self.Filter_Detatched.emit(Filter)

##### Search Function ######
            
    def getFilters(self, uuid=-1, inputUUID=-1, pathNo=-1, filterType=None):
        outList = list()
        for Filter in self.filterList:
            if(Filter.filterSettings['uuid'] != uuid and uuid != -1):
                continue
            if(Filter.filterSettings['inputSource'] != inputUUID and inputUUID != -1):
                continue
            if(Filter.filterSettings['inputSourcePathNo'] != pathNo and pathNo != -1):
                continue
            if(filterType is not None):
                if(issubclass(filterType, Filter) is False): #AnalogFilter or DigitalFilter
                    continue
            outList.append(Filter)
        return outList

    def getSources(self, uuid=-1, sourceType=None):
        outList = list()
        for source in self.getSourceObjs():
            if(source.sourceSettings['uuid'] != uuid and uuid != -1):
                continue
            if(sourceType is not None):
                if(isinstance(source, sourceType) is False):
                    continue
            outList.append(source)
        return outList

    def getTrigCompsRefUUID(self, uuid):
        return self.ds.iM.getTrigCompsRefUUID(uuid)
    
    def removeCompByUUID(self, uuid):
        return self.ds.iM.removeCompByUUID(uuid)

    def getHardwareObjectByUUID(self, uuid):
        for deviceHandler in self.devoceHandlerList:
            if(deviceHandler.Get_Standard_Field('uuid') == uuid):
                return deviceHandler
        return None        

    def getSourceObjs(self):
        sourceList = list()
        for deviceHandler in self.deviceHandlerList:
            sourceList += deviceHandler.Get_Sources()

        return sourceList

    def getFilterModelFromIdentifier(self, identifier):
        for filter in self.filtersAvailable:
            if(filter.filterIdentifier == identifier):
                return filter
        
        return None

    def findHardwareModelByIdentifier(self, identifier):
        for hardwareModel in self.driversAvailable:
            if(hardwareModel.hardwareIdentifier == identifier):
                return hardwareModel
        return None

##### Initialization Functions #####

    def loadFilters(self):
        self.ds.postLog('Loading User Filters... ', DSConstants.LOG_PRIORITY_HIGH)

        for root, dirs, files in os.walk(self.filtersDir):
            for name in files:
                url = os.path.join(root, name)
                filterHolder = self.loadFilterFromFile(url)
                if (filterHolder != None):
                    self.filtersAvailable.append(filterHolder)

        self.ds.postLog('Finished Loading User Filters!', DSConstants.LOG_PRIORITY_HIGH)

    def loadHardwareDrivers(self):
        self.ds.postLog('Loading Hardware Drivers... ', DSConstants.LOG_PRIORITY_HIGH)

        for root, dirs, files in os.walk(self.hardwareDriverDir):
            for name in files:
                url = os.path.join(root, name)
                driverHolder = self.loadDriverFromFile(url)
                if (driverHolder != None):
                    self.driversAvailable.append(driverHolder)

        self.ds.postLog('Finished Loading Hardware Drivers!', DSConstants.LOG_PRIORITY_HIGH)

    def loadLabviewInterface(self):
        self.ds.postLog('Initializing DataStation Labview Interface... ', DSConstants.LOG_PRIORITY_HIGH)
        self.lvInterface = DataStation_LabviewExtension(self.ds)
        self.ds.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)

    def loadFilterFromFile(self, filepath):
        class_inst = None
        expected_class = 'User_Filter'
        py_mod = None
        mod_name, file_ext = os.path.splitext(os.path.split(filepath)[-1])
        loaded = False

        if file_ext.lower() == '.py':
            self.ds.postLog('   Found Filter Script: ' + filepath, DSConstants.LOG_PRIORITY_MED)
            py_mod = imp.load_source(mod_name, filepath)
        else:
            return

        if (py_mod != None):
            if hasattr(py_mod, expected_class):  # verify that Filter is a class in this file
                loaded = True
                class_temp = getattr(py_mod, expected_class)(filepath)
                class_temp.hM = self
                class_temp.ds = self.ds
                class_temp.iM = self.ds.iM
                if isinstance(class_temp, Filter):  # verify that Filter inherits the correct class
                    class_inst = class_temp

        if(loaded):
            self.ds.postLog('  (Success!)', DSConstants.LOG_PRIORITY_MED, newline=False)
        else:
            self.ds.postLog(' (Failed!)', DSConstants.LOG_PRIORITY_MED, newline=False)

        class_inst.hM = self
        #class_inst.setupWidgets()
        class_inst.onCreationParent()
        return class_inst

    def loadDriverFromFile(self, filepath):
        class_inst = None
        py_mod = None
        mod_name, file_ext = os.path.splitext(os.path.split(filepath)[-1])
        loaded = False

        if file_ext.lower() == '.py':
            self.ds.postLog('   Found Hardware Driver: ' + filepath, DSConstants.LOG_PRIORITY_MED)
            py_mod = imp.load_source(mod_name, filepath)
        else:
            return

        if (py_mod != None):
            if(hasattr(py_mod, mod_name) is True):
                class_temp = getattr(py_mod, mod_name)(None, dict(), dict(), list(), list())
                if issubclass(type(class_temp), HardwareDevice):  # verify that driver inherits the correct class
                    class_inst = class_temp
                    loaded = True
                
        if(loaded):
            self.ds.postLog('  (Success!)', DSConstants.LOG_PRIORITY_MED, newline=False)
        else:
            self.ds.postLog(' (Failed!)', DSConstants.LOG_PRIORITY_MED, newline=False)

        return class_inst

##### Filter Manipulation Functions #####

    def loadFilterFromData(self, filterInputSource, data, pathNo):
        if('filterIdentifier' in data):
            model = self.getFilterModelFromIdentifier(data['filterIdentifier'])
            newFilter = self.addFilter(model)
            if(newFilter is not None):
                newFilter.onLoad(data)
                #newFilter.Attach_Input(filterInputSource, pathNo)
            else:
                self.ds.postLog('Attempting To Restore Filter With Identifier (' + data['filterIdentifier'] + ') But Could Not Find Matching User_Filter... ', DSConstants.LOG_PRIORITY_HIGH)
            return newFilter
        return None

    def addFilter(self, filterModel, loadData=None):
        if(filterModel is not None):
            newFilter = type(filterModel)(self)
            newFilter.ds = self.ds
            newFilter.iM = self.iM
            newFilter.hM = self
            newFilter.wM = self.wM
            newFilter.onCreationParent()
            self.filterList.append(newFilter)

            if(loadData is not None):
                newFilter.loadPacket(loadData)

            self.ds.postLog('Added Filter: ' + newFilter.Get_Type(), DSConstants.LOG_PRIORITY_MED)
            self.Filter_Added.emit(newFilter)
            return newFilter
        return None

##### Hardware Manipulation Functions #####

    def programAllDevices(self):
        pass

    def addDigitalTriggerComp(self, hardwareObj):
        triggerComp = self.ds.iM.addCompToInstrument(Digital_Trigger_Component)
        triggerComp.onConnect(hardwareObj.hardwareSettings['name'], hardwareObj.hardwareSettings['uuid'])
        return triggerComp

    def addHardwareObj(self, deviceModel, loadData=None):
        #tempHardware = type(hardwareModel)(self)
        newHandler = HardwareDeviceHandler(self.ds, type(deviceModel), loadData)
        self.deviceHandlerList.append(newHandler)
        self.Hardware_Added.emit(newHandler)
        newHandler.initDeviceThread(self.lvInterface.devices)

        return True

    def removeHardwareObj(self, deviceHandler):
        deviceHandler.onRemove()
        self.deviceHandlerList.remove(deviceHandler)

##### Hardware State ######
    def saveHardwareState(self):
        self.ds.postLog('Recording Hardware State... ', DSConstants.LOG_PRIORITY_HIGH)
        savePacket = dict()
        savePacket['hardwareStates'] = list()
        savePacket['filters'] = list()

        for deviceHandler in self.deviceHandlerList:
            savePacket['hardwareStates'].append(deviceHandler.savePacket())

        for Filter in self.filterList:
            savePacket['filters'].append(Filter.savePacket())

        self.writeHardwareStateFile(savePacket)

        self.ds.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH)

    def writeHardwareStateFile(self, stateData):
        self.ds.postLog('Updating Settings File... ', DSConstants.LOG_PRIORITY_HIGH)
        with open(self.hardwareStatePath, 'w') as file:
            json.dump(stateData, file, sort_keys=True, indent=4)
        self.ds.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)

    #def loadHardwareState(self):
    #    self.ds.postLog('Restoring Hardware State... ', DSConstants.LOG_PRIORITY_HIGH)
    #    if('hardwareState' in self.wM.settings):
    #        tempHardwareSettings = self.wM.settings['hardwareState']
    #        self.ds.wM.settings['hardwareState'] = None
    #        if(self.processHardwareData(tempHardwareSettings) is True):
    #            self.ds.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)
    #        else:
    #            self.ds.postLog('Error Loading Hardware State - Aborting!', DSConstants.LOG_PRIORITY_HIGH, newline=False)
    #    else:
    #        self.ds.postLog('No Hardware State Found - Aborting!', DSConstants.LOG_PRIORITY_HIGH, newline=False)
    #
    #    self.Hardware_State_Loaded.emit()

    def loadHardwareState(self):
        self.ds.postLog('Loading Hardware State Data.. ', DSConstants.LOG_PRIORITY_HIGH)
        if(os.path.isfile(self.hardwareStatePath)):
            with open(self.hardwareStatePath, 'r+') as stateFile:
                try:
                    stateData = json.load(stateFile)
                    stateFile.close()
                    self.ds.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)
                except ValueError:
                    stateData = None
                    self.ds.postLog('Hardware State File is Corrupt!!! Ignoring..', DSConstants.LOG_PRIORITY_HIGH)
            if(stateData is not None):
                self.processHardwareData(stateData)
        else:
            self.ds.postLog('Hardware State File Not Found! Ignoring..', DSConstants.LOG_PRIORITY_HIGH)
        
        self.Hardware_State_Loaded.emit()

    def processHardwareData(self, hardwareData):
        if(hardwareData is not None and 'hardwareStates' in hardwareData):
            for state in hardwareData['hardwareStates']:
                if(('hardwareIdentifier') in state):
                    hardwareModel = self.findHardwareModelByIdentifier(state['hardwareIdentifier'])
                    if(hardwareModel is not None):
                        self.addHardwareObj(hardwareModel, loadData=state)
                    else:
                        self.ds.postLog('Hardware Component State Found (Identifier: ' + state['hardwareIdentifier'] + ') But No Drivers Are Present For This Identifier! Partial Hardware State Import Continuing...', DSConstants.LOG_PRIORITY_HIGH)
                        
                else:
                    self.ds.postLog('Hardware Component State Data Corrupted! Partial Hardware State Import Continuing...', DSConstants.LOG_PRIORITY_HIGH)

            for filterState in hardwareData['filters']:
                if(('filterIdentifier') in filterState):
                    filterModel = self.getFilterModelFromIdentifier(filterState['filterIdentifier'])
                    if(filterModel is not None):
                        self.addFilter(filterModel, loadData=filterState)
                    else:
                        self.ds.postLog('Filter State Found (Identifier: ' + filterState['filterIdentifier'] + ') But No Filter Models Are Present For This Identifier! Partial Hardware State Import Continuing...', DSConstants.LOG_PRIORITY_HIGH)
                else:
                    self.ds.postLog('Filter State Data Corrupted! Partial Hardware State Import Continuing...', DSConstants.LOG_PRIORITY_HIGH)
            return True
        else:
            return False