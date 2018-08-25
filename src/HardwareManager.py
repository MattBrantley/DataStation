import os, sys, imp
from Instrument import *
from Constants import DSConstants as DSConstants
from Filter import Filter
from Hardware_Driver import Hardware_Object
from Sources import *
from Sockets import *
import json as json
from DSWidgets.controlWidget import readyCheckPacket

class HardwareManager():
    hardwareList = list()
    sourceObjList = list()
    filterList = list()
    filtersAvailable = list()
    driversAvailable = list()
    hardwareLoaded = list()

    def __init__(self, workspace, filterURL, driverURL):
        self.workspace = workspace
        self.mainWindow = self.workspace.mainWindow
        self.filterURL = filterURL
        self.driverURL = driverURL
        self.loadFilters()
        self.loadHardwareDrivers()

    def loadHardwareDrivers(self):
        self.mainWindow.postLog('Loading Hardware Drivers... ', DSConstants.LOG_PRIORITY_HIGH)

        for root, dirs, files in os.walk(self.driverURL):
            for name in files:
                url = os.path.join(root, name)
                driverHolder = self.loadDriverFromFile(url)
                if (driverHolder != None):
                    self.driversAvailable.append(driverHolder)

        self.mainWindow.postLog('Finished Loading Hardware Drivers!', DSConstants.LOG_PRIORITY_HIGH)

    def loadDriverFromFile(self, filepath):
        class_inst = None
        expected_class = 'Hardware_Driver'
        py_mod = None
        mod_name, file_ext = os.path.splitext(os.path.split(filepath)[-1])
        loaded = False

        if file_ext.lower() == '.py':
            self.mainWindow.postLog('   Found Hardware Driver: ' + filepath, DSConstants.LOG_PRIORITY_MED)
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
            self.mainWindow.postLog('  (Success!)', DSConstants.LOG_PRIORITY_MED, newline=False)
        else:
            self.mainWindow.postLog(' (Failed!)', DSConstants.LOG_PRIORITY_MED, newline=False)

        class_inst.hardwareManager = self
        return class_inst

    def loadFilters(self):
        self.mainWindow.postLog('Loading User Filters... ', DSConstants.LOG_PRIORITY_HIGH)

        for root, dirs, files in os.walk(self.filterURL):
            for name in files:
                url = os.path.join(root, name)
                filterHolder = self.loadFilterFromFile(url)
                if (filterHolder != None):
                    self.filtersAvailable.append(filterHolder)

        self.mainWindow.postLog('Finished Loading User Filters!', DSConstants.LOG_PRIORITY_HIGH)

    def loadFilterFromFile(self, filepath):
        class_inst = None
        expected_class = 'User_Filter'
        py_mod = None
        mod_name, file_ext = os.path.splitext(os.path.split(filepath)[-1])
        loaded = False

        if file_ext.lower() == '.py':
            self.mainWindow.postLog('   Found Filter Script: ' + filepath, DSConstants.LOG_PRIORITY_MED)
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
            self.mainWindow.postLog('  (Success!)', DSConstants.LOG_PRIORITY_MED, newline=False)
        else:
            self.mainWindow.postLog(' (Failed!)', DSConstants.LOG_PRIORITY_MED, newline=False)

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
                self.workspace.mainWindow.postLog('Attempting To Restore Filter With Identifier (' + data['filterIdentifier'] + ') But Could Not Find Matching User_Filter... ', DSConstants.LOG_PRIORITY_HIGH)
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

    def addHardwareObj(self, hardwareObj):
        self.hardwareLoaded.append(hardwareObj)
        self.mainWindow.hardwareWidget.drawScene()

    def removeHardwareObj(self, hardwareObj):
        hardwareObj.onRemove()
        self.hardwareLoaded.remove(hardwareObj)
        self.mainWindow.hardwareWidget.drawScene()

    def findHardwareModelByIdentifier(self, identifier):
        for hardwareModel in self.driversAvailable:
            if(hardwareModel.hardwareIdentifier == identifier):
                return hardwareModel
        return None

    def loadHardwareState(self):
        self.workspace.mainWindow.postLog('Restoring Hardware State... ', DSConstants.LOG_PRIORITY_HIGH)
        if('hardwareState' in self.workspace.settings):
            tempHardwareSettings = self.workspace.settings['hardwareState']
            self.workspace.settings['hardwareState'] = None
            if(self.processHardwareData(tempHardwareSettings) is True):
                self.mainWindow.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)
            else:
                self.mainWindow.postLog('Error Loading Hardware State - Aborting!', DSConstants.LOG_PRIORITY_HIGH, newline=False)

        else:
            self.mainWindow.postLog('No Hardware State Found - Aborting!', DSConstants.LOG_PRIORITY_HIGH, newline=False)

    def processHardwareData(self, hardwareData):
        if('hardwareStates' in hardwareData):
            for state in hardwareData['hardwareStates']:
                if(('hardwareIdentifier') in state):
                    hardwareModel = self.findHardwareModelByIdentifier(state['hardwareIdentifier'])
                    if(hardwareModel is not None):
                        hardwareObj = self.mainWindow.hardwareWidget.hardwareWidget.addHardware(hardwareModel)
                        if('hardwareSettings' in state):
                            hardwareObj.onLoad(state)
                    else:
                        self.mainWindow.postLog('Hardware Component State Found (Identifier: ' + state['hardwareIdentifier'] + ') But No Drivers Are Present For This Identifier! Partial Hardware State Import Continuing...', DSConstants.LOG_PRIORITY_HIGH)
                        
                else:
                    self.mainWindow.postLog('Hardware Component State Data Corrupted! Partial Hardware State Import Continuing...', DSConstants.LOG_PRIORITY_HIGH)
            return True
        else:
            return False

    def saveHardwareState(self):
        self.workspace.mainWindow.postLog('Recording Hardware State... ', DSConstants.LOG_PRIORITY_HIGH)
        savePacket = dict()
        savePacket['hardwareStates'] = list()

        for hardware in self.hardwareLoaded:
            savePacket['hardwareStates'].append(hardware.onSave())

        self.workspace.settings['hardwareState'] = savePacket

        self.mainWindow.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)

    def onRun(self):
        for hardware in self.hardwareLoaded:
            hardware.onRun()