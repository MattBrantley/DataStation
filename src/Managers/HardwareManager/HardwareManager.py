import os, sys, imp
from Managers.InstrumentManager.Instrument import *
from Managers.InstrumentManager.Filter import Filter
from Managers.InstrumentManager.Sockets import *
from Managers.HardwareManager.Hardware_Object import Hardware_Object
from Managers.HardwareManager.Sources import *
from DataStation_Labview import DataStation_LabviewExtension
from Constants import DSConstants as DSConstants
import json as json
import pyvisa
from DSWidgets.controlWidget import readyCheckPacket

class HardwareManager(QObject):
    Hardware_Modified = pyqtSignal()

    hardwareList = list()
    sourceObjList = list()
    filterList = list()
    filtersAvailable = list()
    driversAvailable = list()
    hardwareLoaded = list()

    def __init__(self, mW):
        super().__init__()
        self.mW = mW
        self.filtersDir = os.path.join(self.mW.rootDir, 'User Filters')
        self.hardwareDriverDir = os.path.join(self.mW.rootDir, 'Hardware Drivers')
        self.loadFilters()
        #self.visaAddresses = self.getVISAObjectsList()
        self.loadHardwareDrivers()
        self.loadLabviewInterface()

        self.mW.DataStation_Closing.connect(self.saveHardwareState)

    def loadLabviewInterface(self):
        self.mW.postLog('Initializing DataStation Labview Interface... ', DSConstants.LOG_PRIORITY_HIGH)
        self.lvInterface = DataStation_LabviewExtension(self.mW)
        self.mW.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)

    def getVISAObjectsList(self): #Because for some reason hte VISA drivers from NI don't locate the devices (even though they are seen in Max...)
        self.mW.postLog('Detecting VISA compatible hardware... ', DSConstants.LOG_PRIORITY_HIGH)
        rm = pyvisa.highlevel.ResourceManager()
        visaAddressList = list()
        for n in range(0, 25):
            for m in range(0, 25):
                try:
                    name = 'PXI' + str(n) + '::' + str(m) + '::INSTR'
                    pxm = rm.open_resource(name)
                    visaAddressList.append(pxm.resource_manufacturer_name)
                except:
                    pass

        self.mW.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)
        return visaAddressList

    def loadHardwareDrivers(self):
        self.mW.postLog('Loading Hardware Drivers... ', DSConstants.LOG_PRIORITY_HIGH)

        for root, dirs, files in os.walk(self.hardwareDriverDir):
            for name in files:
                url = os.path.join(root, name)
                driverHolder = self.loadDriverFromFile(url)
                if (driverHolder != None):
                    self.driversAvailable.append(driverHolder)

        self.mW.postLog('Finished Loading Hardware Drivers!', DSConstants.LOG_PRIORITY_HIGH)

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
                if isinstance(class_temp, Hardware_Object):  # verify that Filter inherits the correct class
                    class_inst = class_temp

        if(loaded):
            self.mW.postLog('  (Success!)', DSConstants.LOG_PRIORITY_MED, newline=False)
        else:
            self.mW.postLog(' (Failed!)', DSConstants.LOG_PRIORITY_MED, newline=False)

        class_inst.hardwareManager = self
        return class_inst

    def loadFilters(self):
        self.mW.postLog('Loading User Filters... ', DSConstants.LOG_PRIORITY_HIGH)

        for root, dirs, files in os.walk(self.filtersDir):
            for name in files:
                url = os.path.join(root, name)
                filterHolder = self.loadFilterFromFile(url)
                if (filterHolder != None):
                    self.filtersAvailable.append(filterHolder)

        self.mW.postLog('Finished Loading User Filters!', DSConstants.LOG_PRIORITY_HIGH)

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
                if isinstance(class_temp, Filter):  # verify that Filter inherits the correct class
                    class_inst = class_temp

        if(loaded):
            self.mW.postLog('  (Success!)', DSConstants.LOG_PRIORITY_MED, newline=False)
        else:
            self.mW.postLog(' (Failed!)', DSConstants.LOG_PRIORITY_MED, newline=False)

        class_inst.hardwareManager = self
        #class_inst.setupWidgets()
        class_inst.onCreationParent()
        return class_inst

    def getSourceObjs(self):
        self.sourceObjList.clear()
        for hardware in self.hardwareLoaded:
            for source in hardware.sourceList:
                self.sourceObjList.append(source)

        return self.sourceObjList

    def linkSources(self):
        for obj in self.getSourceObjs():
            obj.onLink()

    def getFilterModelFromIdentifier(self, identifier):
        for filter in self.filtersAvailable:
            if(filter.filterIdentifier == identifier):
                return filter
        
        return None

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

    def objFromUUID(self, uuid):
        for Filter in self.filterList:
            if(Filter.uuid == uuid):
                return Filter
        for source in self.getSourceObjs():
            if(source.uuid == uuid):
                return source

        return None

    def readyCheck(self):
        subs = list()
        for hardware in self.hardwareLoaded:
            subs.append(hardware.readyCheck())

        return readyCheckPacket('Hardware Manager', DSConstants.READY_CHECK_READY, subs=subs)

    def hardwareModified(self, hardwareObj):
        print('HARDWAWRE WAS MODIFIED')
        print(type(hardwareObj))
        print('HARDWARE_MODIFIED.emit()')
        self.Hardware_Modified.emit()

    def addHardwareObj(self, hardwareObj):
        self.hardwareLoaded.append(hardwareObj)
        hardwareObj.Config_Modified.connect(self.hardwareModified)
        print('HARDWARE_MODIFIED.emit()')
        self.Hardware_Modified.emit()

    def removeHardwareObj(self, hardwareObj):
        hardwareObj.onRemove()
        self.hardwareLoaded.remove(hardwareObj)
        print('HARDWARE_MODIFIED.emit()')
        self.Hardware_Modified.emit()

    def findHardwareModelByIdentifier(self, identifier):
        for hardwareModel in self.driversAvailable:
            if(hardwareModel.hardwareIdentifier == identifier):
                return hardwareModel
        return None

    def loadHardwareState(self):
        self.mW.postLog('Restoring Hardware State... ', DSConstants.LOG_PRIORITY_HIGH)
        if('hardwareState' in self.mW.workspaceManager.settings):
            tempHardwareSettings = self.mW.workspaceManager.settings['hardwareState']
            self.mW.workspaceManager.settings['hardwareState'] = None
            if(self.processHardwareData(tempHardwareSettings) is True):
                self.mW.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)
            else:
                self.mW.postLog('Error Loading Hardware State - Aborting!', DSConstants.LOG_PRIORITY_HIGH, newline=False)
            print('HARDWARE_MODIFIED.emit()')
            self.Hardware_Modified.emit()
        else:
            self.mW.postLog('No Hardware State Found - Aborting!', DSConstants.LOG_PRIORITY_HIGH, newline=False)

    def processHardwareData(self, hardwareData):
        if(hardwareData is not None and 'hardwareStates' in hardwareData):
            for state in hardwareData['hardwareStates']:
                if(('hardwareIdentifier') in state):
                    hardwareModel = self.findHardwareModelByIdentifier(state['hardwareIdentifier'])
                    if(hardwareModel is not None):
                        hardwareObj = self.mW.hardwareWidget.hardwareWidget.addHardware(hardwareModel)
                        if('hardwareSettings' in state):
                            hardwareObj.onLoadParent(state)
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
            savePacket['hardwareStates'].append(hardware.onSave())

        self.mW.workspaceManager.settings['hardwareState'] = savePacket

        self.mW.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)

    def onRun(self):
        for hardware in self.hardwareLoaded:
            hardware.onRun()