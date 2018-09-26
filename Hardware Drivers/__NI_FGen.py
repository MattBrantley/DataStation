from src.Managers.HardwareManager.hardwareObject import hardwareObject, hardwareWorker, hwm
from src.Managers.HardwareManager.Sources import *
from PyQt5.Qt import *
import os, traceback, math, numpy as np, nifgen
from multiprocessing import Process, Queue, Pipe

class Hardware_Driver(hardwareObject):
    hardwareType = 'NI_FGen'
    hardwareIdentifier = 'NI_FGen_MRB'
    hardwareVersion = '1.0'
    hardwareCreator = 'Matthew R. Brantley'
    hardwareVersionDate = '9/4/2018'

    ##### SUPPORT FUNCTIONS #####
    def getDeviceInfo(self):
        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        if(self.hardwareSettings['deviceName'] in self.getDeviceList()):
            with nifgen.Session(self.hardwareSettings['deviceName']) as session:
                self.maxRate = session.arb_sample_rate

    ##### REQUIRED FUNCTIONS #####
    def genSources(self):
        self.clearSourceList()
        if(self.hardwareSettings['deviceName'] in self.getDeviceList()):

            print(self.hardwareSettings['deviceName'])
            with nifgen.Session(self.hardwareSettings['deviceName']) as session:
                for i in range(0, 2): #For some reason fgen doesn't have .channel_count despite the docs saying it does..
                    source = AOSource(self, '['+self.hardwareSettings['deviceName']+'] Output '+str(i), -10, 10, 0.1, 'Output '+str(i))
                    self.addSource(source)
        else:
            #self.Config_Modified.emit(self)
            self.hM.configModified(self)

    def getDeviceList(self): 
        deviceList = list()
        devices = self.hM.lvInterface.devices['NI-FGEN']
        for device in devices:
            deviceList.append(device['Device Name'])

        return deviceList

    def initHardwareWorker(self):
        self.hardwareWorker = NI_FGenHardwareWorker()

    def hardwareObjectConfigWidget(self):
        hardwareConfig = QWidget()
        return hardwareConfig

    def onCreation(self):
        self.hardwareSettings['deviceName'] = ''

    def onLoad(self, loadPacket):
        pass
        # Any hardwareSettings specifically saved by this device are contained in loadPacket

    def onInitialize(self):
        self.hardwareWorker.outQueues['command'].put(hwm(action='init'))
        self.getDeviceInfo()
        self.genSources()
        self.triggerModes['Software'] = True
        self.triggerModes['Digital Rise'] = True
        self.triggerModes['Digital Fall'] = True

    def onProgram(self):
        programmingData = self.parseProgramData()
        if(programmingData is not None):
            print('FGEN PROGRAMMING -----------------------------------------')
            print(programmingData['channelList'])
            print(programmingData['freq'])
            print(programmingData['yAxis'].shape)
            self.hardwareWorker.outQueues['command'].put(hwm(action='config'))
            self.hardwareWorker.outQueues['command'].put(hwm(action='program'))

    def onRun(self):
        self.hardwareWorker.outQueues['command'].put(hwm(action='run'))

class NI_FGenHardwareWorker(hardwareWorker):
    def __init__(self):
        self.initialized = False
        self.configured = False
        self.programmed = False
        self.armed = False
        super().__init__()

    def onConfig(self, msgIn, queueOut):
        resp = hwm(action='textUpdate', msg='CONFIG!')
        queueOut.put(resp)

    def onCommand(self, msgIn, queueOut):

        if(msgIn.action == 'readyCheck'):
            response = 'readyCheck'
        else:
            response = 'textUpdate'

        if(self.armed is False and msgIn.action in ('readyCheck', 'run')):
            queueOut.put(hwm(action=response, msg='Hardware Not Armed', data=False))
            return
        if(self.programmed is False and msgIn.action in ('readyCheck', 'run', 'arm')):
            queueOut.put(hwm(action=response, msg='Hardware Not Programmed', data=False))
            return
        if(self.configured is False and msgIn.action in ('readyCheck', 'run', 'arm', 'program')):
            queueOut.put(hwm(action=response, msg='Hardware Not Configured', data=False))
            return
        if(self.configured is False and msgIn.action in ('readyCheck', 'run', 'arm', 'program', 'configure')):
            queueOut.put(hwm(action=response, msg='Hardware Not Initialized', data=False))
            return
        if(msgIn.action == 'readyCheck'):
            queueOut.put(hwm(action='readyCheck', msg='Hardware Ready!', data=True))
            return


        ##### INITILIAZATION
        if(msgIn.action == 'init'):
            queueOut.put(hwm(action='textUpdate', msg='Initializing..'))
            self.initialized = True
            queueOut.put(hwm(action='textUpdate', msg='Done! Ready for Configuration..'))

        #### CONFIGURING
        if(msgIn.action == 'config'):
            queueOut.put(hwm(action='textUpdate', msg='Configuring..'))
            self.configured = True
            queueOut.put(hwm(action='textUpdate', msg='Done! Ready for Waveform Programming..'))

        ##### PROGRAMMING
        if(msgIn.action == 'program'):
            queueOut.put(hwm(action='textUpdate', msg='Writing Program to Card..'))
            self.programmed = True
            queueOut.put(hwm(action='textUpdate', msg='Done! Ready for Trigger Arming..'))

        ##### ARM
        if(msgIn.action == 'arm'):
            queueOut.put(hwm(action='textUpdate', msg='Writing Program to Card..'))
            self.armed = True
            queueOut.put(hwm(action='textUpdate', msg='Done! DAQ is Armed and Ready!'))

        ##### RUN
        if(msgIn.action == 'run'):
            queueOut.put(hwm(action='textUpdate', msg='Running!', data=False))