from Hardware_Driver import Hardware_Object, hardwareWorker, hwm
from PyQt5.Qt import *
from Sources import *
import os, traceback
import numpy as np
import nidaqmx.system
from multiprocessing import Process, Queue, Pipe

class Hardware_Driver(Hardware_Object):
    hardwareType = 'NI_DAQmx'
    hardwareIdentifier = 'NI_DAQmx_MRB'
    hardwareVersion = '1.0'
    hardwareCreator = 'Matthew R. Brantley'
    hardwareVersionDate = '8/18/2018'

    def onCreation(self):
        self.hardwareSettings['deviceName'] = ''
        self.genSources()

    def hardwareObjectConfigWidget(self):
        hardwareConfig = QWidget()
        hardwareConfig.setMinimumWidth(200)
        hardwareConfig.setMinimumHeight(300)

        layout = QFormLayout()
        hardwareConfig.setLayout(layout)
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

        return hardwareConfig

    def getDeviceList(self):
        system = nidaqmx.system.System.local()
        deviceList = list()
        for device in system.devices:
            deviceList.append(device.name)

        return deviceList

    def updateDevice(self, text):
        self.hardwareSettings['deviceName'] = text
        self.hardwareSettings['name'] = self.hardwareSettings['deviceName']
        self.genSources()

    def afterLoad(self, loadPacket):
        self.genSources()

    def genSources(self):
        self.clearSourceList()
        if(self.hardwareSettings['deviceName'] in self.getDeviceList()):
            device = nidaqmx.system.Device(self.hardwareSettings['deviceName'])
            self.forceNoUpdatesOnSourceAdd(True) #FOR SPEED!
            for chan in device.ai_physical_chans:
                source = DCSource(self, '['+self.hardwareSettings['deviceName']+'] '+chan.name, -10, 10, 0.1, chan.name)
                self.addSource(source)
            self.forceNoUpdatesOnSourceAdd(False) #Have to turn it off or things go awry!

    def parseProgramData(self, programDataList):
        
        print(programDataList)

    def onProgram(self):
        print('I would program now')

    def onRun(self):
        self.program()
        self.hardwareWorker.outQueues['command'].put(hwm(action='run'))

    def initHardwareWorker(self):
        self.hardwareWorker = NI_DAQmHardwareWorker()

class NI_DAQmHardwareWorker(hardwareWorker):
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
        if(msgIn.action == 'init'):
            queueOut.put(hwm(action='textUpdate', msg='Initializing..'))
            self.initialized = True
            queueOut.put(hwm(action='textUpdate', msg='Done! Ready for Configuration..'))

        if(msgIn.action == 'config'):
            queueOut.put(hwm(action='textUpdate', msg='Configuring..'))
            self.configured = True
            queueOut.put(hwm(action='textUpdate', msg='Done! Ready for Waveform Programming..'))

        if(msgIn.action == 'program'):
            queueOut.put(hwm(action='textUpdate', msg='Writing Program to Card..'))
            self.programmed = True
            queueOut.put(hwm(action='textUpdate', msg='Done! Ready for Trigger Arming..'))

        if(msgIn.action == 'arm'):
            queueOut.put(hwm(action='textUpdate', msg='Writing Program to Card..'))
            self.armed = True
            queueOut.put(hwm(action='textUpdate', msg='Done! DAQ is Armed and Ready!'))


        if(msgIn.action == 'run'):
            if(self.initialized is False):
                queueOut.put(hwm(action='textUpdate', msg='ERROR! Hardware Not Initialized', data=False))
                return
            if(self.configured is False):
                queueOut.put(hwm(action='textUpdate', msg='ERROR! Hardware Not Configured', data=False))
                return
            if(self.programmed is False):
                queueOut.put(hwm(action='textUpdate', msg='ERROR! Hardware Not Programmed', data=False))
                return
            if(self.armed is False):
                queueOut.put(hwm(action='textUpdate', msg='ERROR! Hardware Not Armed', data=False))
                return
            queueOut.put(hwm(action='textUpdate', msg='Running!', data=False))

        if(msgIn.action == 'readyCheck'):
            if(self.initialized is False):
                queueOut.put(hwm(action='readyCheck', msg='Hardware Not Initialized', data=False))
                return
            if(self.configured is False):
                queueOut.put(hwm(action='readyCheck', msg='Hardware Not Configured', data=False))
                return
            if(self.programmed is False):
                queueOut.put(hwm(action='readyCheck', msg='Hardware Not Programmed', data=False))
                return
            if(self.armed is False):
                queueOut.put(hwm(action='readyCheck', msg='Hardware Not Armed', data=False))
                return
