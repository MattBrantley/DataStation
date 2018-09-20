from PyQt5.Qt import *
import os, uuid, time, sys, numpy as np
from multiprocessing import Process, Queue, Pipe
from src.Constants import DSConstants as DSConstants, readyCheckPacket
from src.Managers.HardwareManager.Sources import *
from src.Managers.InstrumentManager.Sockets import *

class HardwareDeviceHandler(QObject):
    initialize = pyqtSignal()
    configure = pyqtSignal()
    program = pyqtSignal(list)
    softTrigger = pyqtSignal()
    deviceChanged = pyqtSignal(str)

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

############################################################################################
#################################### INTERNAL USER ONLY ####################################

    def __init__(self, mW, deviceModel):
        super().__init__()
        self.deviceModel = deviceModel

        self.mW = mW
        self.iM = mW.iM
        self.hM = mW.hM
        self.wM = mW.wM

        self.hardwareSettings = dict()
        self.deviceList = list()
        self.sourceList = list()


    def initDeviceThread(self, deviceInformation):
        self.deviceThread = self.deviceModel(deviceInformation, self.hardwareSettings, self.deviceList, self.sourceList)

        ##### Incoming Messages #####
        self.deviceThread.measurementPacket.connect(self.measurementPacket)
        self.deviceThread.initialized.connect(self.initialized)
        self.deviceThread.statusMessage.connect(self.statusMessage)
        self.deviceThread.sourceAdded.connect(self.sourceAdded)

        ##### Outgoing Messages #####
        self.initialize.connect(self.deviceThread.initialize)
        self.deviceChanged.connect(self.deviceThread.deviceChanged)

        self.deviceThread.start()
        self.initialize.emit()

##################################### SIGNAL HANDLERS #####################################

    def sourceAdded(self, source):
        source.registerHWare(self)
        self.hM.sourceAdded(self, source)

    def measurementPacket(self, packet):
        print('Measurement Packet')

    def initialized(self):
        self.hM.deviceInitialized(self)

    def statusMessage(self, msg):
        print(msg)

##################################### INTERNAL FUNCS #####################################
    def savePacket(self):
        savePacket = dict()
        savePacket['hardwareIdentifier'] = self.hardwareSettings['hardwareIdnetified']
        savePacket['hardwareSettings'] = self.hardwareSettings
        print(self.hardwareSettings)
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

    def loadPacket(self, loadPacket):
        #self.hardwareSettings = {**self.hardwareSettings, **loadPacket['hardwareSettings']}
        self.hardwareSettings = loadPacket['hardwareSettings']
        for key, val in loadPacket['hardwareSettings']:
            self.hardwareSettings[key] = val
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

    def onRemove(self):
        pass # safetly shut down the hardware device

    def readyCheck(self):
        subs = list()
        for source in self.sourceList:
            subs.append(source.readyCheck())

        return readyCheckPacket('Device Handler', DSConstants.READY_CHECK_READY, subs=subs)
 
    def programDataReceived(self, source):
        self.hM.programmingModified(self, source)
        self.program.emit(list())

class HardwareDevice(QThread):
    hardwareType = 'HardwareDevice'
    hardwareIdentifier = 'HD_Base'
    hardwareVersion = '1.0'
    hardwareCreator = 'Matthew R. Brantley'
    hardwareVersionDate = '8/20/2018'

    measurementPacket = pyqtSignal(object)
    initialized = pyqtSignal()
    statusMessage = pyqtSignal(str)
    sourceAdded = pyqtSignal(object)
    deviceFound = pyqtSignal(str)

############################################################################################
###################################### OVERRIDE THESE ######################################
    def initialize(self):
        pass

    def device(self, deviceName):
        pass

    def configure(self):
        pass

    def program(self, eventList):
        pass

    def softTrigger(self):
        pass

############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################
            
    def Add_AISource(self, name, vMin, vMax, prec):
        source = AISource('['+self.hardwareSettings['deviceName']+'] '+name, vMin, vMax, prec, name)
        self.addSource(source)

    def Add_AOSource(self, name, vMin, vMax, prec):
        source = AOSource('['+self.hardwareSettings['deviceName']+'] '+name, vMin, vMax, prec, name)
        self.addSource(source)

    def Add_DISource(self, name, trigger=True):
        source = DISource('['+self.hardwareSettings['deviceName']+'] '+name, name, trigger=True)
        self.addSource(source)

    def Add_DOSource(self, name):
        source = DOSource('['+self.hardwareSettings['deviceName']+'] '+name, name)
        self.addSource(source)

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
        self.hardwareSettings['hardwareIdnetified'] = self.hardwareIdentifier
        self.deviceList = deviceList
        self.sourceList = sourceList
        self.runThread = True

    def deviceChanged(self, deviceName):
        self.hardwareSettings['deviceName'] = deviceName
        self.device(deviceName)

    def addSource(self, source):
        self.sourceList.append(source)
        self.sourceAdded.emit(source)

    def addDevice(self, device):
        self.deviceList.append(device['Device Name'])

    def run(self):
        while(self.runThread is True):
            self.usleep(5) #change to usleep()!    