from PyQt5.Qt import *
import os, uuid, time, sys, numpy as np
from multiprocessing import Process, Queue, Pipe
from src.Constants import DSConstants as DSConstants, readyCheckPacket
from src.Managers.HardwareManager.Sources import *
from src.Managers.InstrumentManager.Sockets import *

class HardwareDeviceHandler(QObject):
    scan = pyqtSignal()
    initialize = pyqtSignal()
    configure = pyqtSignal()
    program = pyqtSignal(list)
    softTrigger = pyqtSignal()
    shutdown = pyqtSignal()
    idleState = pyqtSignal()

    deviceChanged = pyqtSignal(str)
    loadPacket = pyqtSignal(dict)

############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################
    def Get_Standard_Field(self, field):
        if(field in self.hardwareSettings):
            return self.hardwareSettings[field]
        else:
            return None

    def Get_Available_Devices(self):
        return self.deviceList

    def Get_Sources(self):
        return self.sourceList

    def Load_Device(self, deviceName):
        self.loadDevice(deviceName)

    def Ready_Status(self):
        return self.hardwareReadyStatus

    def Set_Ready_Status(self, bool):
        self.readyStatus(bool)

############################################################################################
#################################### INTERNAL USER ONLY ####################################
    def __init__(self, ds, deviceModel, loadData):
        super().__init__()
        self.deviceModel = deviceModel
        self.loadData = loadData
        self.deferredProgramming = True
        self.programPackets = list()
        self.hardwareReadyStatus = False

        self.ds = ds
        self.iM = ds.iM
        self.hM = ds.hM
        self.wM = ds.wM

        self.hardwareSettings = dict()
        self.deviceList = list()
        self.sourceList = list()

        #self.iM.Sequence_Unloaded.connect(self.toggleDeferredProgrammingOn)
        self.iM.Sequence_Loaded.connect(self.toggleDeferredProgrammingOff)
        self.ds.DataStation_Closing.connect(self.shutdown)

    def initDeviceThread(self, deviceInformation):
        self.deviceThread = self.deviceModel(deviceInformation, self.hardwareSettings, self.deviceList, self.sourceList)
        self.thread = QThread()

        ##### Incoming Messages #####
        self.deviceThread.scanned.connect(self.scanned)
        self.deviceThread.initialized.connect(self.initialized)
        self.deviceThread.configured.connect(self.configured)
        self.deviceThread.programmed.connect(self.programmed)
        self.deviceThread.softTriggered.connect(self.softTriggered)

        self.deviceThread.measurementPacket.connect(self.measurementPacket)
        self.deviceThread.statusMessage.connect(self.statusMessage)
        self.deviceThread.readyStatus.connect(self.readyStatus)
        self.deviceThread.sourceAdded.connect(self.sourceAdded)
        self.deviceThread.deviceFound.connect(self.deviceFound)

        self.deviceThread.moveToThread(self.thread)

        ##### Outgoing Messages #####
        self.scan.connect(self.deviceThread.scan)
        self.initialize.connect(self.deviceThread.initialize)
        self.configure.connect(self.deviceThread.configure)
        self.program.connect(self.deviceThread.program)
        self.softTrigger.connect(self.deviceThread.softTrigger)
        self.shutdown.connect(self.deviceThread.shutdown)
        self.idleState.connect(self.deviceThread.idleState)

        self.deviceChanged.connect(self.deviceThread.deviceChanged)
        self.loadPacket.connect(self.deviceThread.loadPacket)

        self.thread.start()

        self.scan.emit()
        if(self.loadData is not None):
            self.loadPacket.emit(self.loadData)

##################################### SIGNAL HANDLERS #####################################
    def scanned(self):
        self.hM.hardwareScanned(self)

    def initialized(self):
        self.idleState.emit()
        self.hM.hardwareInitialized(self)

    def configured(self):
        self.hM.hardwareConfigured(self)

    def programmed(self):
        self.hM.hardwareProgrammed(self)

    def softTriggered(self):
        self.hM.hardwareSoftTriggered(self)

    def sourceAdded(self, source):
        source.registerHWare(self)
        self.hM.sourceAdded(self, source)

    def deviceFound(self, deviceName):
        self.hM.hardwareDeviceFound(self, deviceName)

    def measurementPacket(self, source, measurementPacket):
        source.Push_Measurement_Packet(measurementPacket)

    def statusMessage(self, msg):
        self.hM.hardwareStatusMessage(self, msg)

    def readyStatus(self, bool):
        self.hardwareReadyStatus = bool
        self.hM.hardwareReadyStatusChanged(self, bool)

##################################### INTERNAL FUNCS #####################################

    def toggleDeferredProgrammingOn(self):
        self.deferredProgramming = True

    def toggleDeferredProgrammingOff(self):
        self.deferredProgramming = False
        self.pushProgramming()

    def pushProgramming(self):
        if(self.deferredProgramming is False):
            self.program.emit(self.programPackets)

    def savePacket(self):
        savePacket = dict()
        savePacket['hardwareIdentifier'] = self.hardwareSettings['hardwareIdentifier']
        savePacket['hardwareSettings'] = self.hardwareSettings
        sourceSavePackets = list()
        for source in self.sourceList:
            sourceSavePackets.append(source.savePacket())

        savePacket['sourceList'] = sourceSavePackets
        return savePacket

    def loadDevice(self, deviceName):
        self.selectedDevice = deviceName
        if(deviceName == ''):
            self.hM.deviceSelectionRemoved(self)
        if(deviceName in self.deviceList):
            self.hM.deviceSelectionChanged(self, deviceName)

        self.hardwareSettings['deviceName'] = deviceName
        self.deviceChanged.emit(deviceName)

    def onRemove(self):
        pass # safetly shut down the hardware device

    def onRun(self):
        self.hM.handlerSoftTriggerSent(self)
        self.softTrigger.emit()

    def readyCheck(self):
        subs = list()
        for source in self.sourceList:
            subs.append(source.readyCheck())
        
        if(self.hardwareReadyStatus is True):
            return readyCheckPacket('Device Handler', DSConstants.READY_CHECK_READY, subs=subs)
        else:
            return readyCheckPacket('Device Handler', DSConstants.READY_CHECK_ERROR, msg='Device Not Ready!', subs=subs)
 
    def programDataReceived(self, source):
        self.hM.programmingModified(self, source)

        self.programPackets = list()
        for source in self.sourceList:
            if(source.programmingPacket is not None and source.isConnected()):
                self.programPackets.append({'source': source, 'programmingPacket': source.programmingPacket})
        
        self.pushProgramming()

class HardwareDevice(QObject):
    hardwareType = 'HardwareDevice'
    hardwareIdentifier = 'HD_Base'
    hardwareVersion = '1.0'
    hardwareCreator = 'Matthew R. Brantley'
    hardwareVersionDate = '8/20/2018'

    scanned = pyqtSignal()
    initialized = pyqtSignal()
    configured = pyqtSignal()
    programmed = pyqtSignal()
    softTriggered = pyqtSignal()

    measurementPacket = pyqtSignal(object, object) # source, measurementPacket
    statusMessage = pyqtSignal(str)
    readyStatus = pyqtSignal(bool)
    sourceAdded = pyqtSignal(object)
    deviceFound = pyqtSignal(str)

############################################################################################
###################################### OVERRIDE THESE ######################################
    def scan(self):
        pass

    def initialize(self, deviceName):
        pass

    def configure(self):
        pass

    def program(self, eventList):
        pass

    def softTrigger(self):
        pass

    def shutdown(self):
        pass

    def idle(self):
        pass

############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################
    def Get_Standard_Field(self, field):
        if(field in self.hardwareSettings):
            return self.hardwareSettings[field]
        else:
            return None

    def Send_Status_Message(self, msg):
        self.statusMessage.emit(msg)

    def Add_AISource(self, name, vMin, vMax, prec):
        source = AISource('['+self.hardwareSettings['deviceName']+'] '+name, vMin, vMax, prec, name)
        self.addSource(source)
        return source

    def Add_AOSource(self, name, vMin, vMax, prec):
        source = AOSource('['+self.hardwareSettings['deviceName']+'] '+name, vMin, vMax, prec, name)
        self.addSource(source)
        return source

    def Add_DISource(self, name, trigger=True):
        source = DISource('['+self.hardwareSettings['deviceName']+'] '+name, name, trigger=True)
        self.addSource(source)
        return source

    def Add_DOSource(self, name):
        source = DOSource('['+self.hardwareSettings['deviceName']+'] '+name, name)
        self.addSource(source)
        return source

    def Add_Device(self, deviceName):
        self.addDevice(deviceName)

    def Set_Ready_Status(self, status):
        self.readyStatusCopy = status
        self.readyStatus.emit(status)

    def Ready_Status(self):
        return self.readyStatusCopy

    def Push_Measurements_Packet(self, source, measurementPacket):
        self.measurementPacket.emit(source, measurementPacket)

############################################################################################
#################################### INTERNAL USER ONLY ####################################
    def __init__(self, systemDeviceInfo, hardwareSettings, deviceList, sourceList):
        super().__init__()
        self.systemDeviceInfo = systemDeviceInfo
        self.hardwareSettings = hardwareSettings
        self.hardwareSettings['name'] = ''
        self.hardwareSettings['physID'] = ''
        self.hardwareSettings['uuid'] = str(uuid.uuid4())
        self.hardwareSettings['triggerCompUUID'] = ''
        self.hardwareSettings['triggerMode'] =  ''
        self.hardwareSettings['hardwareType'] = self.hardwareType
        self.hardwareSettings['deviceName'] = ''
        self.hardwareSettings['hardwareIdentifier'] = self.hardwareIdentifier

        self.deviceList = deviceList
        self.sourceList = sourceList
        self.runThread = True
        self.readyStatusCopy = False

    @pyqtSlot()
    def idleState(self):
        self.idle()
        QTimer().singleShot(1, self.idleState)

    def deviceChanged(self, deviceName):
        self.hardwareSettings['deviceName'] = deviceName
        self.initialize(deviceName)

    def addSource(self, source):
        self.sourceList.append(source)
        self.sourceAdded.emit(source)

    def addDevice(self, deviceName):
        self.deviceList.append(deviceName)
        self.deviceFound.emit(deviceName)

    def loadPacket(self, loadPacket):
        for key, val in loadPacket['hardwareSettings'].items():
            self.hardwareSettings[key] = val

        self.initialize(self.hardwareSettings['deviceName'])

        if('sourceList' in loadPacket):
            self.loadSourceData(loadPacket['sourceList'])

    def loadSourceData(self, sourceData):
        if(sourceData is not None):
            for loadPacket in sourceData:
                if('physConID' in loadPacket):                                  # This has to happen AFTER sources are generated
                    source = self.getSourceByPhysConID(loadPacket['physConID']) # Source generation is dynamic, only load a source if it's physConID matches!
                    if(source is not None):
                        source.loadPacket(loadPacket)

    def getSourceByPhysConID(self, physConID):
        for source in self.sourceList:
            if(source.sourceSettings['physConID'] == physConID):
                return source
        return None