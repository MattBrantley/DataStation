from Hardware_Driver import Hardware_Object, hardwareWorker, hwm
from PyQt5.Qt import *
from Sources import *
import os, traceback, math
import numpy as np
import nidaqmx.system
from multiprocessing import Process, Queue, Pipe

class Hardware_Driver(Hardware_Object):
    hardwareType = 'NI_DAQmx'
    hardwareIdentifier = 'NI_DAQmx_MRB'
    hardwareVersion = '1.0'
    hardwareCreator = 'Matthew R. Brantley'
    hardwareVersionDate = '8/18/2018'

    ##### SUPPORT FUNCTIONS #####
    def getDeviceInfo(self):
        if(self.hardwareSettings['deviceName'] in self.getDeviceList()):
            device = nidaqmx.system.Device(self.hardwareSettings['deviceName'])
            try:
                self.maxRate = device.ao_max_rate
            except nidaqmx.errors.DaqError:
                self.maxRate = None

    def getDeviceList(self):
        system = nidaqmx.system.System.local()
        deviceList = list()
        for device in system.devices:
            deviceList.append(device.name)

        return deviceList

    def updateDevice(self, text):
        self.hardwareSettings['deviceName'] = text
        self.hardwareSettings['name'] = self.hardwareSettings['deviceName']
        self.onInitialize() #Resets the instrument
        #self.genSources()

    def genSources(self):
        self.clearSourceList()
        if(self.hardwareSettings['deviceName'] in self.getDeviceList()):
            device = nidaqmx.system.Device(self.hardwareSettings['deviceName'])
            self.forceNoUpdatesOnSourceAdd(True) #FOR SPEED!
            for chan in device.ao_physical_chans:
                source = DCSource(self, '['+self.hardwareSettings['deviceName']+'] '+chan.name, -10, 10, 0.1, chan.name)
                self.addSource(source)
            self.forceNoUpdatesOnSourceAdd(False) #Have to turn it off or things go awry!

    def parseProgramData(self):
        eventData = self.getEvents()

        if(len(eventData) != 0):
            channelList = list()
            timingBounds = self.getTimingBounds(eventData)
            granularity = round(self.getGranularity(eventData), int(math.log10(self.maxRate)))
            freq = 1/granularity
            #print('STARTINGGGGGG')
            #print(timingBounds)
            #print(granularity)
            xAxis = np.arange(timingBounds['min'], timingBounds['max'] + granularity, granularity)
            #print(xAxis)
            #print(xAxis.shape)
            yAxisData = None
            for dataPacket in eventData:
                if(dataPacket.waveformData is None):
                    break
                channelList.append(dataPacket.physicalConnectorID)
                yAxis = np.interp(xAxis, dataPacket.waveformData[:,0], dataPacket.waveformData[:,1])
                if(yAxisData is None):
                    yAxisData = yAxis
                else:
                    yAxisData = np.vstack((yAxisData, yAxis))
                #xAxis = np.hstack((xAxis, yAxis))
                #print(dataPacket.physicalConnectorID)
                #print(dataPacket.waveformData)
            if(yAxisData is not None):
                yAxisData = np.transpose(yAxisData)
                #print(yAxisData.shape)
            
            dataOut = dict()
            dataOut['channelList'] = channelList
            dataOut['yAxis'] = yAxisData
            dataOut['freq'] = freq
            return dataOut
        else:
            return None

    def getTimingBounds(self, programDataList):
        xMin = None
        xMax = None
        for dataPacket in programDataList:
            if(dataPacket.waveformData is None):
                break
            tempXMin = dataPacket.waveformData[:,0].min()
            tempXMax = dataPacket.waveformData[:,0].max()
            if(xMin == None or xMin > tempXMin):
                xMin = tempXMin
            if(xMax == None or xMax < tempXMax):
                xMax = tempXMax
        bounds = dict()
        bounds['min'] = xMin
        bounds['max'] = xMax
        return bounds
    
    def getGranularity(self, programDataList):
        gran = None
        for dataPacket in programDataList:
            if(dataPacket.waveformData is None):
                break
            diffs = np.ediff1d(dataPacket.waveformData[:,0])
            minDiff = diffs.min()
            if(gran == None or gran > minDiff):
                gran = minDiff
        return gran

    ##### REQUIRED FUNCTIONS #####
    def initHardwareWorker(self):
        self.hardwareWorker = NI_DAQmHardwareWorker()

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

    def onCreation(self):
        self.hardwareSettings['deviceName'] = ''

    def onLoad(self, loadPacket):
        pass
        # Any hardwareSettings specifically saved by this device are contained in loadPacket

    def onInitialize(self):
        self.getDeviceInfo()
        self.genSources()

    def onProgram(self):
        programmingData = self.parseProgramData()
        print(programmingData)
        if(programmingData is not None):
            self.hardwareWorker.outQueues['command'].put(hwm(action='program'))

    def onRun(self):
        #self.onProgram()
        self.hardwareWorker.outQueues['command'].put(hwm(action='run'))

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