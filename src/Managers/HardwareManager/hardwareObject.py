from PyQt5.Qt import *
import os, uuid, time, sys
from multiprocessing import Process, Queue, Pipe
from Constants import DSConstants as DSConstants
from Managers.HardwareManager.Sources import *
from Managers.InstrumentManager.Sockets import *
from DSWidgets.networkViewWidget import netObject

import numpy as np
from DSWidgets.controlWidget import readyCheckPacket

# This is so that pickle can pull the correct class
sys.path.append(str(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))) + '\\Hardware Drivers\\')

class hardwareObject(QObject):
    hardwareType = 'Default Hardware Object'
    hardwareIdentifier = 'DefHardObj'
    hardwareVersion = '1.0'
    hardwareCreator = 'Matthew R. Brantley'
    hardwareVersionDate = '8/18/2018'

############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################

    def Get_Sources(self):
        return self.sourceList

    def Get_Sources_By_Type(self, sourceType):
        return [s for s in self.sourceList if isinstance(s, sourceType)]

    def Clear_Sources(self):
        self.clearsourceList()

    def Add_AISource(self, name, vMin, vMax, prec):
        source = AISource(self, '['+self.hardwareSettings['deviceName']+'] '+name, vMin, vMax, prec, name)
        self.addSource(source)
        self.hM.sourceAdded(self, source)

    def Add_AOSource(self, name, vMin, vMax, prec):
        source = AOSource(self, '['+self.hardwareSettings['deviceName']+'] '+name, vMin, vMax, prec, name)
        self.addSource(source)
        self.hM.sourceAdded(self, source)

    def Add_DISource(self, name, trigger=True):
        source = DISource(self, '['+self.hardwareSettings['deviceName']+'] '+name, name, trigger=True)
        self.addSource(source)
        self.hM.sourceAdded(self, source)

    def Add_DOSource(self, name):
        source = DOSource(self, '['+self.hardwareSettings['deviceName']+'] '+name, name)
        self.addSource(source)
        self.hM.sourceAdded(self, source)

############################################################################################
#################################### INTERNAL USER ONLY ####################################

    def __init__(self, hM, modelObject=False, **kwargs):
        super().__init__()
        self.hM = hM
        self.hardwareSettings = {}
        self.hardwareSettings['name'] = ''
        self.hardwareSettings['physID'] = ''
        self.hardwareSettings['uuid'] = str(uuid.uuid4())
        self.hardwareSettings['triggerCompUUID'] = ''
        self.hardwareSettings['triggerMode'] = ''
        self.hardwareSettings['hardwareType'] = self.hardwareType
        self.sourceList = list()
        self.managerMessages = list()
        self.initTriggerModes()
        self.onCreationParent()
        self.triggerComponent = None
        
        self.workerReady = False
        self.workerReadyMessage = 'Worker Not Started!'

##### DataStation Interface Functions #####

    def readyCheck(self):
        subs = list()
        for source in self.sourceList:
            subs.append(source.readyCheck())

        return readyCheckPacket('Hardware Object', DSConstants.READY_CHECK_READY, subs=subs)

    def getUUID(self):
        return self.hardwareSettings['uuid']

##### Functions Called By Factoried Sources #####

    def program(self, source):
        self.hM.program(self, source)

    def clearSourceList(self):
        self.sourceList = list()

##### Functions Over-Ridden By hardwareObjects #####

    def initHardwareWorker(self): ### OVERRIDE ME!! ####
        self.hardwareWorker = hardwareWorker()

    def initTriggerModes(self): ### OVERRIDE ME!! ####
        self.triggerModes = dict()
        self.triggerModes['Software'] = True
        self.triggerModes['Digital Rise'] = False
        self.triggerModes['Digital Fall'] = False

    def getDeviceList(self): ### OVERRIDE ME!! ####
        return list()

    def hardwareObjectConfigWidgetParent(self):
        configWidget = QWidget()
        configLayout = QVBoxLayout()
        configWidget.setLayout(configLayout)
        #configWidget.setMinimumHeight(350)
        configWidget.setMinimumWidth(200)

        hardwareConfig = QWidget()

        layout = QFormLayout()
        hardwareConfig.setLayout(layout)

        if('deviceName' in self.hardwareSettings):
            recoverDeviceTemp = self.hardwareSettings['deviceName'] #Temp fix - updateDevice called at start was whiping deviceName
        deviceSelection = QComboBox()
        deviceSelection.addItem('')
        index = 0
        for item in self.getDeviceList():
            index = index + 1
            deviceSelection.addItem(item)
            if(item == recoverDeviceTemp):
                deviceSelection.setCurrentIndex(index)
        #Doing this after solved the issue of rebuilding the instrument every time widget was shown
        deviceSelection.currentTextChanged.connect(self.updateDevice)
        layout.addRow("Device:", deviceSelection)

        if('triggerMode' in self.hardwareSettings):
            recoverDeviceTemp = self.hardwareSettings['triggerMode'] #Temp fix - updateDevice called at start was whiping deviceName
        triggerSelection = QComboBox()
        index = 0
        for key, val in self.triggerModes.items():
            if(val is True):
                index = index + 1
                triggerSelection.addItem(key)
                if(key == recoverDeviceTemp):
                    triggerSelection.setCurrentIndex(index-1)
        triggerSelection.currentTextChanged.connect(self.updateTrigger)

        layout.addRow("Trigger:", triggerSelection)

        configLayout.addWidget(hardwareConfig)
        driverConfig = self.hardwareObjectConfigWidget()
        if(isinstance(driverConfig, QWidget)):
            configLayout.addWidget(driverConfig)

        return configWidget

    def hardwareObjectConfigWidget(self): ### OVERRIDE ME!! ####
        return 0

    def onCreationParent(self):
        self.onCreation()

    def onCreation(self): ### OVERRIDE ME!! ####
        pass

    def loadPacketParent(self, loadPacket):
        self.hardwareSettings = {**self.hardwareSettings, **loadPacket['hardwareSettings']}
        if('sourceList' in loadPacket):
            sourceListData = loadPacket['sourceList']
            if(sourceListData is not None):
                for loadPacket in sourceListData:
                    if('physConID' in loadPacket):                                  # This has to happen AFTER sources are generated
                        source = self.getSourceByPhysConID(loadPacket['physConID']) # Source generation is dynamic, only load a source if it's physConID matches!
                        if(source is not None):
                            source.loadPacket(loadPacket)
        self.onLoad(loadPacket)
        self.resetDevice()

    def onLoad(self, loadPacket): ### OVERRIDE ME!! ####
        pass

    def onInitialize(self): ### OVERRIDE ME!! ####
        pass

    def onProgramParent(self):
        self.onProgram()

    def onProgram(self): ### OVERRIDE ME!! ####
        pass

##### TRIGGER COMPONENT ######

    def updateTrigger(self, text):
        self.hardwareSettings['triggerMode'] = text
        self.generateTriggerComponent(text)

    def generateTriggerComponent(self, text):
        self.removeTriggerComponent()
        if(self.hardwareSettings['deviceName'] != ''):
            if(text in ('Digital Rise', 'Digital Fall')):
                #self.triggerSource = DISocket()
                self.triggerComponent = self.hM.addDigitalTriggerComp(self)
                self.hardwareSettings['triggerCompUUID'] = self.triggerComponent.compSettings['uuid']
                msg = hwm(msg='[Manager]: Digital Trigger Component Generated')
                self.managerMessages.append(msg)
            elif(text == 'Software'):
                #self.triggerSource = DISocket()
                msg = hwm(msg='[Manager]: Software Trgiger Enabled')
                self.hardwareSettings['triggerCompUUID'] = ''
                self.managerMessages.append(msg)

        #self.Trigger_Modified.emit(self)
        self.hM.triggerModified(self)

    def removeTriggerComponent(self):
        print(self.hardwareSettings['triggerCompUUID'])
        self.hM.removeCompByUUID(self.hardwareSettings['triggerCompUUID'])
        self.hardwareSettings['triggerCompUUID'] = ''

    def verifyTriggerComponentExists(self):
        if(self.hM.getTrigCompsRefUUID(self.hardwareSettings['uuid']) is None):
            self.updateTrigger(self.hardwareSettings['triggerMode'])

##### Search Functions #####

    def getSourceByPhysConID(self, physConID):
        for source in self.sourceList:
            if(source.sourceSettings['physConID'] == physConID):
                return source
        return None

    def getEvents(self):
        programDataList = list()
        for source in self.sourceList:
            result = source.getProgramData()
            if(result is not None):
                programDataList.append(result)

        return programDataList

##### hardwareObject Manipulation Functions #####

    def updateDevice(self, text):
        self.hardwareSettings['deviceName'] = text
        self.hardwareSettings['name'] = self.hardwareSettings['deviceName']
        self.resetDevice()

    def resetDevice(self):
        self.newMgrMsg()
        #self.removeTriggerComponent()
        if(self.hardwareSettings['deviceName'] not in self.getDeviceList() and self.hardwareSettings['deviceName'] != ''):
            self.mgrMsg('Device ' + self.hardwareSettings['deviceName'] + ' is not recognized. Resettings hardware driver!')
            self.hardwareSettings['deviceName'] = ''
        
        if(self.hardwareSettings['deviceName'] != ''):
            self.onInitialize()

    def savePacket(self):
        savePacket = dict()
        savePacket['hardwareIdentifier'] = self.hardwareIdentifier
        savePacket['hardwareSettings'] = self.hardwareSettings
        sourceSavePackets = list()
        for source in self.sourceList:
            sourceSavePackets.append(source.savePacket())

        savePacket['sourceList'] = sourceSavePackets
        return savePacket

    def addSource(self, source):
        self.sourceList.append(source)
        self.mgrMsg('Source added: ' + str(type(source)))
        self.hM.configModified(self)

##### hardwareWorker Functions #####

    def getMessages(self):
        messageList = list()
        messageList = self.managerMessages + self.hardwareWorker.updateWorkerResponses()
        self.managerMessages.clear()
        return messageList

    def getPingTime(self):
        return self.hardwareWorker.checkPing()

    def onRun(self):
        self.hardwareWorker.outQueues['command'].put(hwm(action='run'))

    def mgrMsg(self, text):
        msg = hwm(msg='[Manager]: ' + text)
        self.managerMessages.append(msg)

    def newMgrMsg(self):
        msg = hwm(msg='[Manager]: Device Reset', action='refresh')
        self.managerMessages.append(msg)

class hardwareWorker():
    def __init__(self):
        self.pingList = list()
        self.pingAverageCount = 5

        self.inQueues = {   'response': Queue(),
                            'measurement': Queue(),
                            'pong': Queue(),
                        }
        
        self.outQueues = {   'config': Queue(),
                            'command': Queue(),
                            'ping': Queue()
                        }

        self.initProcess()

    def initProcess(self):        
        self.process = Process(group=None, name='Hardware Worker', target=self.runWorker, args=(self.inQueues, self.outQueues, ))
        self.process.daemon = True
        self.process.start()

    def checkPing(self):
        pingStr = str(uuid.uuid4())
        pingMsg = hwm(action='ping', msg=pingStr, data=int(round(time.time()*1000)))
        self.outQueues['ping'].put(pingMsg)

        while(self.inQueues['pong'].empty() is False):
            pongMsg = self.inQueues['pong'].get()
            self.pingList.append(pongMsg.data)
            if(len(self.pingList) > self.pingAverageCount):
                self.pingList.pop(0)
            
        summer = 0
        for val in self.pingList:
            summer = summer + val

        avgPing = summer/self.pingAverageCount
        return avgPing

    def updateWorkerResponses(self):
        responseList = list()
        while(self.inQueues['response'].empty() is False):
            msg = self.inQueues['response'].get()
            msg.msg = '[Worker]: ' + msg.msg
            responseList.append(msg)

        return responseList

    def runWorker(self, msgOut, msgIn):
        die = False
        while(die is False):
            time.sleep(0.05)
            if(msgIn['ping'].empty() is False):
                self.onPing(msgIn['ping'].get(), msgOut['pong'])
            if(msgIn['config'].empty() is False):
                self.onConfig(msgIn['config'].get(), msgOut['response'])
            if(msgIn['command'].empty() is False):
                self.onCommand(msgIn['command'].get(), msgOut['response'])

    def onPing(self, msgIn, queueOut):
        queueOut.put(hwm(action='pong', msg=msgIn.msg, data=int(round(time.time()*1000))-msgIn.data))

    def onConfig(self, msgIn, queueOut):
        resp = hwm(action='textUpdate', msg='Hardware_Driver does not implement config()!')
        queueOut.put(resp)

    def onCommand(self, msgIn, queueOut):
        resp = hwm(action='textUpdate', msg='Hardware_Driver does not implement command()!')
        queueOut.put(resp)

class hwm():
    def __init__(self, action='', msg='', data=None):
        self.action = action
        self.msg = msg
        self.data = data

class hardwareObjectConfigWidget(QWidget):
    def __init__(self, hM, Hardware_Object):
        super().__init__()
        self.hM = hM
        self.Hardware_Object = Hardware_Object