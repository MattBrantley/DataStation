import os, sys, imp
from Managers.InstrumentManager.Instrument import *
from Managers.InstrumentManager.Filter import *
from Managers.InstrumentManager.Sockets import *
from Managers.InstrumentManager.Digital_Trigger_Component import Digital_Trigger_Component
from Managers.HardwareManager.hardwareObject import hardwareObject
from Managers.HardwareManager.Sources import *
from DataStation_Labview import DataStation_LabviewExtension
from Constants import DSConstants as DSConstants
import json as json
from DSWidgets.controlWidget import readyCheckPacket

class HardwareManager(QObject):

############################################################################################
##################################### EXTERNAL SIGNALS #####################################

##### Signals: Hardware State #####
    Hardware_State_Loaded = pyqtSignal()
    Hardware_State_Saving = pyqtSignal()

##### Signals: Hardware #####
    Hardware_Added = pyqtSignal(object) # hardwareObj
    Hardware_Removed = pyqtSignal()
    Hardware_Trigger_Modified = pyqtSignal()

##### Signals: Sequence #####
    Sequence_Started = pyqtSignal()
    Sequence_Finished = pyqtSignal()

##### Signals: Sources #####
    Source_Added = pyqtSignal(object, object) # hardwareObj, sourceObj

############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################

##### Functions: Instrument Manager #####
    def Do_Ready_Check(self):
        return self.readyCheck()

    def Ready_Check_Status(self):
        return self.readyStatus

    def Run_Sequence(self):
        self.onRun()

##### Functions: Hardware Models #####

    def Get_Hardware_Models_Available(self):
        return self. driversAvailable

##### Functions: Hardware #####
    def Get_Hardware(self):
        return self.hardwareLoaded

    def Add_Hardware(self, hardwareModel):
        return self.addHardwareObj(hardwareModel)

    def Remove_Hardware(self, hardwareObject):
        return self.removeHardwareObj(hardwareObject)

    def Get_All_Sources(self):
        reList = list()
        for hardware in self.hardwareLoaded:
            reList += hardware.Get_Sources()
        return reList

    def Get_All_Sources_By_Type(self, sourceType):
        reList = list()
        for hardware in self.hardwareLoaded:
            reList += hardware.Get_Sources_By_Type(sourceType)
        return reList
        

############################################################################################
#################################### INTERNAL USER ONLY ####################################
    def __init__(self, mW):
        super().__init__()

        self.mW = mW
        self.readyStatus = False
        self.filtersDir = os.path.join(self.mW.rootDir, 'User Filters')
        self.hardwareDriverDir = os.path.join(self.mW.rootDir, 'Hardware Drivers')
        self.filtersAvailable = list()
        self.driversAvailable = list()
        self.hardwareLoaded = list()
        self.sourceObjList = list()
        self.filterList = list()

        self.mW.DataStation_Closing.connect(self.saveHardwareState)

    def connections(self, iM, wM):
        self.iM = self.mW.iM
        self.wM = self.mW.wM
        #self.iM.Instrument_Loaded.connect(self.instrumentLoaded)
        #self.iM.Sequence_Loaded.connect(self.programAllDevices)
        #self.iM.Instrument_Unloaded.connect(self.instrumentUnloaded)

##### DataStation Reserved Functions #####

    def readyCheck(self):
        subs = list()
        self.readyStatus = True
        for hardware in self.hardwareLoaded:
            check = hardware.readyCheck()
            subs.append(check)
            if(check.readyStatus is False):
                self.readyStatus = False

        return readyCheckPacket('Hardware Manager', DSConstants.READY_CHECK_READY, subs=subs)

##### Functions Called By Factoried Hardware_Objects #####

    def configModified(self, hWare):
        pass

    def program(self, hWare, source):
        pass

    def triggerModified(self, hWare):
        pass

    def sourceAdded(self, hardwareObj, sourceObj): # Source_Added
        self.Source_Added.emit(hardwareObj, sourceObj)

##### Search Function ######

    def getFilterOrSourceByUUID(self, uuid):
        for Filter in self.filterList:
            if(Filter.uuid == uuid):
                return Filter
        for source in self.getSourceObjs('All'):
            if(source.getUUID() == uuid):
                return source

        return None
            
    def getFiltersWithUUIDAsInput(self, uuid):
        for Filter in self.filterList:
            if(Filter.uuid == uuid):
                return Filter

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
        expected_class = 'Hardware_Driver'
        py_mod = None
        mod_name, file_ext = os.path.splitext(os.path.split(filepath)[-1])
        loaded = False

        if file_ext.lower() == '.py':
            self.mW.postLog('   Found Hardware Driver: ' + filepath, DSConstants.LOG_PRIORITY_MED)
            py_mod = imp.load_source(mod_name, filepath)
        else:
            return

        if (py_mod != None):
            if hasattr(py_mod, expected_class):  # verify that Filter is a class in this file
                loaded = True
                class_temp = getattr(py_mod, expected_class)(filepath)
                if isinstance(class_temp, hardwareObject):  # verify that Filter inherits the correct class
                    class_inst = class_temp

        if(loaded):
            self.mW.postLog('  (Success!)', DSConstants.LOG_PRIORITY_MED, newline=False)
        else:
            self.mW.postLog(' (Failed!)', DSConstants.LOG_PRIORITY_MED, newline=False)

        class_inst.hM = self
        return class_inst

    def getFiltersByType(self, typeText):
        typeOut = type(None)
        if(typeText == 'Sockets: Analog Output'):
            typeOut = AnalogFilter
        elif(typeText == 'Sockets: Analog Input'):
            typeOut = AnalogFilter
        elif(typeText == 'Sockets: Digital Output'):
            typeOut = DigitalFilter
        elif(typeText == 'Sockets: Digital Input'):
            typeOut = DigitalFilter

        filterList = list()
        for filterClass in self.filtersAvailable:
            if(issubclass(filterClass, typeOut) or typeText == 'All'):
                filterList.append()

    def getTrigCompsRefUUID(self, uuid):
        return self.mW.iM.getTrigCompsRefUUID(uuid)
    
    def removeCompByUUID(self, uuid):
        return self.mW.iM.removeCompByUUID(uuid)

    def getHardwareObjectByUUID(self, uuid):
        for hardware in self.hardwareLoaded:
            if(hardware.hardwareSettings['uuid'] == uuid):
                return hardware
        return None        

    def getSourceObjs(self, typeText):
        typeOut = type(None)
        if(typeText == 'Sockets: Analog Output'):
            typeOut = AOSource
        elif(typeText == 'Sockets: Analog Input'):
            typeOut = AISource
        elif(typeText == 'Sockets: Digital Output'):
            typeOut = DOSource
        elif(typeText == 'Sockets: Digital Input'):
            typeOut = DISource

        self.sourceObjList.clear()
        for hardware in self.hardwareLoaded:
            for source in hardware.sourceList:
                if(isinstance(source, typeOut) or typeText == 'All'):
                    self.sourceObjList.append(source)

        return self.sourceObjList

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

##### Filter Manipulation Functions #####

    def loadFilterFromData(self, filterInputSource, data, pathNo):
        if('filterIdentifier' in data):
            model = self.getFilterModelFromIdentifier(data['filterIdentifier'])
            if(model is not None):
                newFilter = type(model)(self)
                newFilter.onCreationParent()
                newFilter.onLoad(data)
                newFilter.filterInputSource = filterInputSource
                newFilter.filterInputPathNo = pathNo
                self.filterList.append(newFilter)
                return newFilter
            else:
                self.mW.postLog('Attempting To Restore Filter With Identifier (' + data['filterIdentifier'] + ') But Could Not Find Matching User_Filter... ', DSConstants.LOG_PRIORITY_HIGH)
        return None

##### Hardware Manipulation Functions #####

    def instrumentLoaded(self):
        for hardwareObj in self.hardwareLoaded:
            hardwareObj.verifyTriggerComponentExists()    
        
    def programAllDevices(self):
        for device in self.hardwareLoaded:
            device.program()

    def addDigitalTriggerComp(self, hardwareObj):
        triggerComp = self.mW.iM.addCompToInstrument(Digital_Trigger_Component)
        triggerComp.onConnect(hardwareObj.hardwareSettings['name'], hardwareObj.hardwareSettings['uuid'])
        return triggerComp

    def addHardwareObj(self, hardwareModel, loadData=None):
        tempHardware = type(hardwareModel)(self)
        tempHardware.initHardwareWorker()

        self.hardwareLoaded.append(tempHardware)

        if(loadData is None):
            tempHardware.resetDevice()
        else:
            tempHardware.loadPacketParent(loadData)

        self.Hardware_Added.emit(tempHardware)
        return tempHardware

    def removeHardwareObj(self, hardwareObj):
        hardwareObj.onRemove()
        self.hardwareLoaded.remove(hardwareObj)

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
                        hardwareObj = self.addHardwareObj(hardwareModel, loadData=state)
                        if('hardwareSettings' in state):
                            hardwareObj.loadPacketParent(state)
                    else:
                        self.mW.postLog('Hardware Component State Found (Identifier: ' + state['hardwareIdentifier'] + ') But No Drivers Are Present For This Identifier! Partial Hardware State Import Continuing...', DSConstants.LOG_PRIORITY_HIGH)
                        
                else:
                    self.mW.postLog('Hardware Component State Data Corrupted! Partial Hardware State Import Continuing...', DSConstants.LOG_PRIORITY_HIGH)
            return True
        else:
            return False

    def saveHardwareState(self):
        self.mW.postLog('Recording Hardware State... ', DSConstants.LOG_PRIORITY_HIGH)
        savePacket = dict()
        savePacket['hardwareStates'] = list()

        for hardware in self.hardwareLoaded:
            savePacket['hardwareStates'].append(hardware.savePacket())

        self.wM.settings['hardwareState'] = savePacket

        self.mW.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)

    def onRun(self):
        self.Sequence_Started.emit()
        for hardware in self.hardwareLoaded:
            hardware.onRun()