from PyQt5.Qt import *
import os, uuid, time, sys
from multiprocessing import Process, Queue, Pipe
from Constants import DSConstants as DSConstants
from Managers.HardwareManager.Sources import *
import numpy as np
from DSWidgets.controlWidget import readyCheckPacket

# This is so that pickle can pull the correct class
sys.path.append(str(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))) + '\\Hardware Drivers\\')

class Hardware_Object(QObject):
    Config_Modified = pyqtSignal(object)
    Reprogrammed = pyqtSignal(object)

    hardwareType = 'Default Hardware Object'
    hardwareIdentifier = 'DefHardObj'
    hardwareVersion = '1.0'
    hardwareCreator = 'Matthew R. Brantley'
    hardwareVersionDate = '8/18/2018'

    def __init__(self, hardwareManager, modelObject=False, **kwargs):
        super().__init__()
        self.sourceListWidget = QListWidget()
        self.hardwareSettings = {}
        self.hardwareSettings['name'] = ''
        self.hardwareSettings['physID'] = ''
        self.hardwareSettings['uuid'] = str(uuid.uuid4())
        self.hardwareManager = hardwareManager
        self.sourceList = list()
        self.onCreationParent()
        self.sourceListData = None
        self.forceNoUpdatesOnSourceAddToggle = False
        
        self.workerReady = False
        self.workerReadyMessage = 'Worker Not Started!'

        #self.pingTimer = QTimer()
        #self.pingTimer.timeout.connect(self.checkReadyWorker)
        #self.pingTimer.start(100)

    def hardwareObjectConfigWidget(self):
        hardwareObjectConfigWidget = QWidget()
        hardwareObjectConfigWidget.setMinimumWidth(200)
        hardwareObjectConfigWidget.setMinimumHeight(300)
        return hardwareObjectConfigWidget

    def initHardwareWorker(self):
        self.hardwareWorker = hardwareWorker()

    def onCreationParent(self):
        self.onCreation()

    def onCreation(self):
        pass

    def getSources(self):
        return self.sourceList
    
    def readyCheck(self):
        subs = list()
        for source in self.sourceList:
            subs.append(source.readyCheck())

        return readyCheckPacket('Hardware Object', DSConstants.READY_CHECK_READY, subs=subs)

    def onSave(self):
        savePacket = dict()
        savePacket['hardwareType'] = self.hardwareType
        savePacket['hardwareIdentifier'] = self.hardwareIdentifier
        savePacket['hardwareSettings'] = self.hardwareSettings

        sourceSavePackets = list()
        for source in self.sourceList:
            sourceSavePackets.append(source.onSave())

        savePacket['sourceList'] = sourceSavePackets

        return savePacket

    def onLoadParent(self, loadPacket):
        self.hardwareSettings = {**self.hardwareSettings, **loadPacket['hardwareSettings']}
        if('sourceList' in loadPacket):
            self.sourceListData = loadPacket['sourceList']
            self.loadSourceListData()
        self.onLoad(loadPacket)
        self.onInitialize()

    def loadSourceListData(self):
        if(self.sourceListData is not None):
            for loadPacket in self.sourceListData:
                if('physConID' in loadPacket):
                    source = self.getSourceByPhysConID(loadPacket['physConID'])
                    if(source is not None):
                        source.onLoad(loadPacket)

    def onInitialize(self):
        pass

    def onLoad(self, loadPacket):
        pass

    def clearSourceList(self):
        for source in self.sourceList:
            source.detachSockets()
        self.sourceList.clear()
        self.updateSourceListWidget()

    def addSource(self, source):
        self.sourceList.append(source)

        if(self.forceNoUpdatesOnSourceAddToggle is False):
            self.loadSourceListData()
            self.updateSourceListWidget()
            self.hardwareManager.mW.instrumentManager.reattachSockets()
            print('Config_Modified.emit()')
            self.Config_Modified.emit(self)

    def forceNoUpdatesOnSourceAdd(self, toggle): #Improves speed to use this when adding many sockets at once
        self.forceNoUpdatesOnSourceAddToggle = toggle
        if(toggle is False): #Turning it off calls these update functions - necessary
            self.loadSourceListData()
            self.updateSourceListWidget()
            self.hardwareManager.mW.instrumentManager.reattachSockets()
            print('Config_Modified.emit()')
            self.Config_Modified.emit(self)

    def updateSourceListWidget(self):
        self.sourceListWidget.clear()
        for source in self.sourceList:
            self.sourceListWidget.addItem(source.name)

    def onRemove(self):
        for source in self.sourceList:
            source.onRemove()

    def getSourceByPhysConID(self, physConID):
        for source in self.sourceList:
            if(source.physicalConnectorID == physConID):
                return source
        return None

    def getWorkerResponses(self):
        return self.hardwareWorker.updateWorkerResponses()

    def getPingTime(self):
        return self.hardwareWorker.checkPing()
        
    def onRun(self):
        self.hardwareWorker.outQueues['command'].put(hwm(action='run'))

    def program(self):
        self.onProgramParent()

    def onProgramParent(self):
        self.onProgram()
        import traceback
        traceback.print_stack()
        #print(programmingData)
        print('Reprogrammed.emit(self)')
        self.Reprogrammed.emit(self)

    def getEvents(self):
        programDataList = list()
        for source in self.sourceList:
            result = source.getProgramData()
            if(result is not None):
                programDataList.append(result)

        return programDataList

    def onProgram(self):
        pass

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

        #self.outQueues['command'].put(hwm(action='init'))
        #self.outQueues['command'].put(hwm(action='config'))
        #self.outQueues['command'].put(hwm(action='program'))
        #self.outQueues['command'].put(hwm(action='arm'))

        self.initProcess()
        #self.pingTimer = QTimer()
        #self.pingTimer.timeout.connect(self.checkPing)
        #self.pingTimer.start(100)

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
    def __init__(self, hardwareManager, Hardware_Object):
        super().__init__()
        self.hardwareManager = hardwareManager
        self.Hardware_Object = Hardware_Object