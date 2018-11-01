from PyQt5.Qt import *
import os, uuid, time, sys, numpy as np
from multiprocessing import Process, Queue, Pipe
from src.Constants import DSConstants as DSConstants, readyCheckPacket
from src.Managers.HardwareManager.Sources import *
from src.Managers.InstrumentManager.Sockets import *

# This is so that pickle can pull the correct class
sys.path.append(str(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))) + '\\Hardware Drivers\\')

class hardwareObject():
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
        self.clearSourceList()

    def Show_Config_Widget(self, pos):
        self.showConfigWidget(pos)

    def Remove_Hardware(self):
        self.hM.Remove_Device(self)

    def Add_AISource(self, name, vMin, vMax, prec):
        source = AISource(self, '['+self.hardwareSettings['deviceName']+'] '+name, vMin, vMax, prec, name)
        self.addSource(source)

    def Add_AOSource(self, name, vMin, vMax, prec):
        source = AOSource(self, '['+self.hardwareSettings['deviceName']+'] '+name, vMin, vMax, prec, name)
        self.addSource(source)

    def Add_DISource(self, name, trigger=True):
        source = DISource(self, '['+self.hardwareSettings['deviceName']+'] '+name, name, trigger=True)
        self.addSource(source)

    def Add_DOSource(self, name):
        source = DOSource(self, '['+self.hardwareSettings['deviceName']+'] '+name, name)
        self.addSource(source)

    
############################################################################################
#################################### INTERNAL USER ONLY ####################################

    def __init__(self, hM, modelObject=False, **kwargs):
        self.ds = None                #Factory does not write this. Hardware manager writes it immediately after init.
        self.iM = None                #Factory does not write this. Hardware manager writes it immediately after init.
        self.wM = None                #Factory does not write this. Hardware manager writes it immediately after init.
        self.hM = None                #Factory does not write this. Hardware manager writes it immediately after init.
        self.hardwareSettings = {}
        self.hardwareSettings['name'] = ''
        self.hardwareSettings['physID'] = ''
        self.hardwareSettings['uuid'] = str(uuid.uuid4())
        self.hardwareSettings['triggerCompUUID'] = ''
        self.hardwareSettings['triggerMode'] = ''
        self.hardwareSettings['hardwareType'] = self.hardwareType
        self.sourceList = list()
        self.initTriggerModes()
        self.onCreationParent()
        self.triggerComponent = None

        self.thread = hardwareThread()
        self.thread.sourceAdded.connect(self.sourceAdded)
        self.thread.start()


##### DataStation Interface Functions #####

    def readyCheck(self):
        subs = list()
        for source in self.sourceList:
            subs.append(source.readyCheck())

        return readyCheckPacket('Hardware Object', DSConstants.READY_CHECK_READY, subs=subs)

    def getUUID(self):
        return self.hardwareSettings['uuid']

##### Slots #####

    def sourceAdded(self):
        #self.sourceList.append(source)
        print('SOURCE WAS ADDED')

##### Functions Called By Factoried Sources #####

    def programDataRecieved(self, source):
        self.hM.programmingModified(self, source)

    def clearSourceList(self):
        for source in reversed(self.sourceList):
            self.hM.sourceRemoved(self, source)
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
        self.resetDevice()
        self.onLoad(loadPacket)
        if('sourceList' in loadPacket):
            self.loadSourceData(loadPacket['sourceList'])

    def onLoad(self, loadPacket): ### OVERRIDE ME!! ####
        pass

    def onInitialize(self): ### OVERRIDE ME!! ####
        pass

    def onProgramParent(self):
        self.onProgram()

    def onProgram(self): ### OVERRIDE ME!! ####
        pass

##### Search Functions #####

    def getEvents(self):
        programDataList = list()
        for source in self.sourceList:
            result = source.getProgramData()
            if(result is not None):
                programDataList.append(result)

        return programDataList

##### hardwareObject Manipulation Functions #####

    def showConfigWidget(self, pos):
        menu = QMenu()
        hardwareConfig = QWidgetAction(self.ds)
        hardwareConfig.setDefaultWidget(self.hardwareObjectConfigWidgetParent())
        menu.addAction(hardwareConfig)

        action = menu.exec_(pos)

    def updateDevice(self, text):
        self.hardwareSettings['deviceName'] = text
        self.hardwareSettings['name'] = self.hardwareSettings['deviceName']
        self.resetDevice()



    def resetDevice(self):
        self.hM.deviceReset(self)
        self.Clear_Sources()
        
        if(self.hardwareSettings['deviceName'] != ''):
            self.onInitialize()


    def addSource(self, source):
        self.sourceList.append(source)


##### hardwareWorker Functions #####

    def getMessages(self):
        messageList = list()
        messageList = self.hardwareWorker.updateWorkerResponses()
        return messageList

    def onRun(self):
        self.hardwareWorker.outQueues['command'].put(hwm(action='run'))



class hardwareWorker():
    def __init__(self):
        self.pingList = list()
        self.pingAverageCount = 5

        self.inQueues = {   'response': Queue(),
                            'measurement': Queue()
                        }
        
        self.outQueues = {   'config': Queue(),
                            'command': Queue()
                        }

        self.initProcess()

    def initProcess(self):        
        self.process = Process(group=None, name='Hardware Worker', target=self.runWorker, args=(self.inQueues, self.outQueues, ))
        self.process.daemon = True
        self.process.start()

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