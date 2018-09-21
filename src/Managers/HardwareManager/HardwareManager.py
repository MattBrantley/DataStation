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

    def Run_Sequence(self):
        for handler in self.deviceHandlerList:
            handler.onRun()

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
    def __init__(self, mW):
        super().__init__()

        self.mW = mW
        self.readyStatus = False
        self.filtersDir = os.path.join(self.mW.rootDir, 'Filters')
        self.hardwareDriverDir = os.path.join(self.mW.rootDir, 'Hardware Drivers')
        self.filtersAvailable = list()
        self.driversAvailable = list()
        self.deviceHandlerList = list()
        self.sourceObjList = list()
        self.filterList = list()

        self.mW.DataStation_Closing.connect(self.saveHardwareState)

    def connections(self, iM, wM):
        self.iM = self.mW.iM
        self.wM = self.mW.wM

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
        return self.mW.iM.getTrigCompsRefUUID(uuid)
    
    def removeCompByUUID(self, uuid):
        return self.mW.iM.removeCompByUUID(uuid)

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
        self.mW.postLog('Loading User Filters... ', DSConstants.LOG_PRIORITY_HIGH)

        for root, dirs, files in os.walk(self.filtersDir):
            for name in files:
                url = os.path.join(root, name)
                filterHolder = self.loadFilterFromFile(url)
                if (filterHolder != None):
                    self.filtersAvailable.append(filterHolder)

        self.mW.postLog('Finished Loading User Filters!', DSConstants.LOG_PRIORITY_HIGH)

    def loadHardwareDrivers(self):
        self.mW.postLog('Loading Hardware Drivers... ', DSConstants.LOG_PRIORITY_HIGH)

        for root, dirs, files in os.walk(self.hardwareDriverDir):
            for name in files:
                url = os.path.join(root, name)
                driverHolder = self.loadDriverFromFile(url)
                if (driverHolder != None):
                    self.driversAvailable.append(driverHolder)

        self.mW.postLog('Finished Loading Hardware Drivers!', DSConstants.LOG_PRIORITY_HIGH)

    def loadLabviewInterface(self):
        self.mW.postLog('Initializing DataStation Labview Interface... ', DSConstants.LOG_PRIORITY_HIGH)
        self.lvInterface = DataStation_LabviewExtension(self.mW)
        self.mW.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)

    def loadFilterFromFile(self, filepath):
        class_inst = None
        expected_class = 'User_Filter'
        py_mod = None
        mod_name, file_ext = os.path.splitext(os.path.split(filepath)[-1])
        loaded = False

        if file_ext.lower() == '.py':
            self.mW.postLog('   Found Filter Script: ' + filepath, DSConstants.LOG_PRIORITY_MED)
            py_mod = imp.load_source(mod_name, filepath)
        else:
            return

        if (py_mod != None):
            if hasattr(py_mod, expected_class):  # verify that Filter is a class in this file
                loaded = True
                class_temp = getattr(py_mod, expected_class)(filepath)
                class_temp.hM = self
                class_temp.mW = self.mW
                class_temp.iM = self.mW.iM
                if isinstance(class_temp, Filter):  # verify that Filter inherits the correct class
                    class_inst = class_temp

        if(loaded):
            self.mW.postLog('  (Success!)', DSConstants.LOG_PRIORITY_MED, newline=False)
        else:
            self.mW.postLog(' (Failed!)', DSConstants.LOG_PRIORITY_MED, newline=False)

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
            self.mW.postLog('   Found Hardware Driver: ' + filepath, DSConstants.LOG_PRIORITY_MED)
            py_mod = imp.load_source(mod_name, filepath)
        else:
            return

        if (py_mod != None):
            if(hasattr(py_mod, mod_name) is True):
                class_temp = getattr(py_mod, mod_name)(dict(), dict(), list(), list())
                if issubclass(type(class_temp), HardwareDevice):  # verify that driver inherits the correct class
                    class_inst = class_temp
                    loaded = True
                
        if(loaded):
            self.mW.postLog('  (Success!)', DSConstants.LOG_PRIORITY_MED, newline=False)
        else:
            self.mW.postLog(' (Failed!)', DSConstants.LOG_PRIORITY_MED, newline=False)

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
                self.mW.postLog('Attempting To Restore Filter With Identifier (' + data['filterIdentifier'] + ') But Could Not Find Matching User_Filter... ', DSConstants.LOG_PRIORITY_HIGH)
            return newFilter
        return None

    def addFilter(self, filterModel, loadData=None):
        if(filterModel is not None):
            newFilter = type(filterModel)(self)
            newFilter.mW = self.mW
            newFilter.iM = self.iM
            newFilter.hM = self
            newFilter.wM = self.wM
            newFilter.onCreationParent()
            self.filterList.append(newFilter)

            if(loadData is not None):
                newFilter.loadPacket(loadData)

            self.mW.postLog('Added Filter: ' + newFilter.Get_Type(), DSConstants.LOG_PRIORITY_MED)
            self.Filter_Added.emit(newFilter)
            return newFilter
        return None

##### Hardware Manipulation Functions #####

    def programAllDevices(self):
        pass

    def addDigitalTriggerComp(self, hardwareObj):
        triggerComp = self.mW.iM.addCompToInstrument(Digital_Trigger_Component)
        triggerComp.onConnect(hardwareObj.hardwareSettings['name'], hardwareObj.hardwareSettings['uuid'])
        return triggerComp

    def addHardwareObj(self, deviceModel, loadData=None):
        #tempHardware = type(hardwareModel)(self)
        newHandler = HardwareDeviceHandler(self.mW, type(deviceModel), loadData)
        self.deviceHandlerList.append(newHandler)
        self.Hardware_Added.emit(newHandler)
        newHandler.initDeviceThread(self.lvInterface.devices)

        return True

    def removeHardwareObj(self, deviceHandler):
        deviceHandler.onRemove()
        self.deviceHandlerList.remove(deviceHandler)

    def loadHardwareState(self):
        self.mW.postLog('Restoring Hardware State... ', DSConstants.LOG_PRIORITY_HIGH)
        if('hardwareState' in self.wM.settings):
            tempHardwareSettings = self.wM.settings['hardwareState']
            self.mW.wM.settings['hardwareState'] = None
            if(self.processHardwareData(tempHardwareSettings) is True):
                self.mW.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)
            else:
                self.mW.postLog('Error Loading Hardware State - Aborting!', DSConstants.LOG_PRIORITY_HIGH, newline=False)
        else:
            self.mW.postLog('No Hardware State Found - Aborting!', DSConstants.LOG_PRIORITY_HIGH, newline=False)

        self.Hardware_State_Loaded.emit()

    def processHardwareData(self, hardwareData):
        if(hardwareData is not None and 'hardwareStates' in hardwareData):
            for state in hardwareData['hardwareStates']:
                if(('hardwareIdentifier') in state):
                    hardwareModel = self.findHardwareModelByIdentifier(state['hardwareIdentifier'])
                    if(hardwareModel is not None):
                        self.addHardwareObj(hardwareModel, loadData=state)
                    else:
                        self.mW.postLog('Hardware Component State Found (Identifier: ' + state['hardwareIdentifier'] + ') But No Drivers Are Present For This Identifier! Partial Hardware State Import Continuing...', DSConstants.LOG_PRIORITY_HIGH)
                        
                else:
                    self.mW.postLog('Hardware Component State Data Corrupted! Partial Hardware State Import Continuing...', DSConstants.LOG_PRIORITY_HIGH)

            for filterState in hardwareData['filters']:
                if(('filterIdentifier') in filterState):
                    filterModel = self.getFilterModelFromIdentifier(filterState['filterIdentifier'])
                    if(filterModel is not None):
                        self.addFilter(filterModel, loadData=filterState)
                    else:
                        self.mW.postLog('Filter State Found (Identifier: ' + filterState['filterIdentifier'] + ') But No Filter Models Are Present For This Identifier! Partial Hardware State Import Continuing...', DSConstants.LOG_PRIORITY_HIGH)
                        
                else:
                    self.mW.postLog('Filter State Data Corrupted! Partial Hardware State Import Continuing...', DSConstants.LOG_PRIORITY_HIGH)
                        

            return True
        else:
            return False

    def saveHardwareState(self):
        self.mW.postLog('Recording Hardware State... ', DSConstants.LOG_PRIORITY_HIGH)
        savePacket = dict()
        savePacket['hardwareStates'] = list()
        savePacket['filters'] = list()

        for deviceHandler in self.deviceHandlerList:
            savePacket['hardwareStates'].append(deviceHandler.savePacket())

        for Filter in self.filterList:
            savePacket['filters'].append(Filter.savePacket())


        self.wM.settings['hardwareState'] = savePacket

        self.mW.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH)