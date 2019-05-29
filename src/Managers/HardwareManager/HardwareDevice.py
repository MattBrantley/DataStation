from PyQt5.Qt import *
import os, uuid, time, sys, numpy as np
from multiprocessing import Process, Queue, Pipe
from src.Constants import DSConstants as DSConstants
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
    stopRun = pyqtSignal()

    deviceChanged = pyqtSignal(str)
    triggerChanged = pyqtSignal(str)
    loadPacket = pyqtSignal(dict)

############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################
    def Get_Standard_Field(self, field):
        if(field in self.hardwareSettings):
            return self.hardwareSettings[field]
        else:
            return None

    def Get_Name(self):
        return self.Get_Standard_Field('deviceName')

    def Get_Current_Trigger_Mode(self):
        return self.Get_Standard_Field('triggerMode')

    def Get_Available_Devices(self):
        return self.deviceList

    def Get_Trigger_Modes(self):
        return self.triggerModeList

    def Get_Sources(self):
        return self.sourceList

    def Load_Device(self, deviceName):
        self.loadDevice(deviceName)

    def Set_Trigger_Mode(self, triggerModeName):
        self.setTriggerMode(triggerModeName)

    def Ready_Status(self):
        return self.hardwareReadyStatus

    def Set_Ready_Status(self, bool):
        self.readyStatus(bool)

    def Set_Active_Instrument(self, instrument):
        self.setActiveInstrument(instrument)

    def Get_Active_Instrument(self):
        return self.activeInstrument

    def Push_Programming(self):
        return self.pushProgramming()

    def Disable_Programming_Lock(self):
        self.progLock = False

    def Enable_Programming_Lock(self):
        self.progLock = True

############################################################################################
#################################### INTERNAL USER ONLY ####################################
    def __init__(self, ds, deviceModel, loadData):
        super().__init__()
        self.deviceModel = deviceModel
        self.loadData = loadData
        self.programPackets = list()
        self.hardwareReadyStatus = False
        self.triggerModeList = list()
        self.deviceComponents = list()
        self.progLock = False

        self.ds = ds
        self.iM = ds.iM
        self.hM = ds.hM
        self.wM = ds.wM

        self.activeInstrument = None

        self.hardwareSettings = dict()
        self.deviceList = list()
        self.sourceList = list()
        self.ds.DataStation_Closing.connect(self.shutdown)

    def initDeviceThread(self, deviceInformation):
        self.deviceThread = self.deviceModel(self, deviceInformation, self.hardwareSettings, self.deviceList, self.sourceList)
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
        self.deviceThread.sourceRemoved.connect(self.sourceRemoved)
        self.deviceThread.triggerModeAdded.connect(self.triggerModeAdded)
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
        self.stopRun.connect(self.deviceThread.stop)

        self.deviceChanged.connect(self.deviceThread.deviceChanged)
        self.triggerChanged.connect(self.deviceThread.triggerChanged)
        self.loadPacket.connect(self.deviceThread.loadPacket)

        self.thread.start()

        self.scan.emit()
        
        if(self.loadData is not None):
            self.loadPacket.emit(self.loadData)

##################################### SIGNAL HANDLERS #####################################
    def scanned(self):
        self.hM.hardwareScanned(self)

    def initialized(self):
        self.hM.hardwareInitialized(self)
        self.idleState.emit()

    def configured(self):
        self.hM.hardwareConfigured(self)

    def programmed(self):
        self.hM.hardwareProgrammed(self)

    def softTriggered(self):
        self.hM.hardwareSoftTriggered(self)

    def sourceAdded(self, source):
        #source.registerHWare(self)
        self.hM.sourceAdded(self, source)

    def sourceRemoved(self, source):
        self.hM.sourceRemoved(self, source)

    def triggerModeAdded(self, triggerModeName):
        self.triggerModeList.append(triggerModeName)
        self.hM.triggerModeAdded(self, triggerModeName)

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

    def setActiveInstrument(self, instrument):
        self.activeInstrument = instrument

    def pushProgramming(self):
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

    def setTriggerMode(self, triggerModeName):
        self.triggerMode = triggerModeName
        self.hardwareSettings['triggerMode'] = triggerModeName
        self.triggerChanged.emit(triggerModeName)
        self.Push_Programming()

    def onRemove(self):
        pass # safetly shut down the hardware device

    def onRun(self):
        self.hM.handlerSoftTriggerSent(self)
        self.softTrigger.emit()

    def onStop(self):
        self.hM.handlerStoppingInstrument(self)
        self.stopRun.emit()

    def readyCheck(self, traceIn):
        trace = traceIn.copy()
        trace.append(self)
        if self.hardwareReadyStatus is False:
            trace[0].Fail_Ready_Check(trace, 'Device Not Ready!')

        if self.Get_Active_Instrument().Get_UUID() != trace[0].Get_UUID():
            trace[0].Warning_Ready_Check(trace, 'Source/Device Is Currently Programmed For Another Instrument')
 
    def programDataReceived(self, source):
        self.deferredProgramDataRecieved(source)
        #self.pushProgramming()

    def deferredProgramDataRecieved(self, source):
        self.hM.programmingModified(self, source)

        self.programPackets = list()
        for source in self.sourceList:
            if(source.programmingPacket is not None and source.isConnected() and source.Get_Programming_Instrument() is self.Get_Active_Instrument()):
                self.programPackets.append({'source': source, 'programmingPacket': source.programmingPacket})


















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
    sourceAdded = pyqtSignal(object) # source
    sourceRemoved = pyqtSignal(object) # source
    triggerModeAdded = pyqtSignal(str) # name
    deviceFound = pyqtSignal(str)

############################################################################################
###################################### OVERRIDE THESE ######################################
    def scan(self):
        pass

    def initialize(self, deviceName, triggerMode):
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

    def stop(self):
        self.Send_Status_Message('Device does not have implemented stop() functionality.')

############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################
    def Get_Standard_Field(self, field):
        if(field in self.hardwareSettings):
            return self.hardwareSettings[field]
        else:
            return None

    def Send_Status_Message(self, msg):
        self.statusMessage.emit(msg)

    def Add_Trigger_Mode(self, name):
        self.triggerModeAdded.emit(name)

    def Get_Device_Name(self):
        return self.Get_Standard_Field('deviceName')

    def Get_Trigger_Mode(self):
        return self.Get_Standard_Field('triggerMode')

    def Set_Triggered_State(self, state):
        if state is True:
            self.isTriggered = True
        else:
            self.isTriggered = False

    def Is_Triggered(self):
        return self.isTriggered

    def Add_AISource(self, name, vMin, vMax, prec):
        source = AISource(self.handler, '['+self.hardwareSettings['deviceName']+'] '+name, vMin, vMax, prec, name)
        self.addSource(source)
        return source

    def Add_AOSource(self, name, vMin, vMax, prec):
        source = AOSource(self.handler, '['+self.hardwareSettings['deviceName']+'] '+name, vMin, vMax, prec, name)
        self.addSource(source)
        return source

    def Add_DISource(self, name):
        source = DISource(self.handler, '['+self.hardwareSettings['deviceName']+'] '+name, name)
        self.addSource(source)
        return source

    def Add_DOSource(self, name):
        source = DOSource(self.handler, '['+self.hardwareSettings['deviceName']+'] '+name, name)
        self.addSource(source)
        return source

    def Add_Digital_Trigger(self, name):
        source = DISource(self.handler, '['+self.hardwareSettings['deviceName']+'] '+name, name, trigger=True)
        self.addSource(source)
        return source

    def Add_Analog_Trigger(self, name, vMin, vMax, prec):
        source = AISource(self.handler, '['+self.hardwareSettings['deviceName']+'] '+name, vMin, vMax, prec, name, trigger=True)
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

    def Get_Handler(self):
        return self.handler

############################################################################################
#################################### INTERNAL USER ONLY ####################################
    def __init__(self, handler, systemDeviceInfo, hardwareSettings, deviceList, sourceList):
        super().__init__()
        self.handler = handler
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
        self.isTriggered = False

        self.loadPacketData = None

    @pyqtSlot()
    def idleState(self):
        self.idle()
        QTimer().singleShot(1, self.idleState)

    def deviceChanged(self, deviceName):
        self.hardwareSettings['deviceName'] = deviceName
        self.initialize(deviceName, self.Get_Trigger_Mode())

    def triggerChanged(self, triggerModeName):
        self.loadPacket(self.loadPacketData, triggerModeChange=triggerModeName)

        for source in self.sourceList:
            for socket in source.Get_Sockets():
                if socket.Get_Component().Get_Instrument() == self.Get_Handler().Get_Active_Instrument():
                    socket.Push_Programming()

    def addSource(self, source):
        source.registerHWare(self.handler)
        self.sourceList.append(source)
        self.sourceAdded.emit(source)

    def addDevice(self, deviceName):
        self.deviceList.append(deviceName)
        self.deviceFound.emit(deviceName)

    def loadPacket(self, loadPacket, triggerModeChange=None):
        self.loadPacketData = loadPacket
        if loadPacket is not None:
            for key, val in loadPacket['hardwareSettings'].items():
                self.hardwareSettings[key] = val

        if triggerModeChange is not None:
            self.hardwareSettings['triggerMode'] = triggerModeChange

        self.clearSources()
        self.initialize(self.hardwareSettings['deviceName'], self.hardwareSettings['triggerMode'])

        if loadPacket is not None:
            if('sourceList' in loadPacket):
                self.loadSourceData(loadPacket['sourceList'])

    def clearSources(self):
        for source in self.sourceList:
            self.sourceRemoved.emit(source)
        self.sourceList.clear()

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