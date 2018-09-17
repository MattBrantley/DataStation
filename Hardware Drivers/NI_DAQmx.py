from Managers.HardwareManager.hardwareObject import hardwareObject, hardwareWorker, hwm
from PyQt5.Qt import *
import os, traceback, math
import numpy as np
import nidaqmx.system
from multiprocessing import Process, Queue, Pipe

class Hardware_Driver(hardwareObject):
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

    def parseProgramData(self):
        eventData = self.getEvents()

        if(len(eventData) != 0):
            channelList = list()
            timingBounds = self.getTimingBounds(eventData)
            gran = self.getGranularity(eventData)
            if(gran is not None):
                granularity = round(self.getGranularity(eventData), int(math.log10(self.maxRate)))
                if(granularity == 0):
                    granularity = 1/self.maxRate
            else:
                return None
            freq = 1/granularity
            xAxis = np.arange(timingBounds['min'], timingBounds['max'] + granularity, granularity)
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
            if(yAxisData is not None):
                yAxisData = np.transpose(yAxisData)
            
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
            if(dataPacket.rate is None):
                diffs = np.ediff1d(dataPacket.waveformData[:,0])
                minDiff = diffs.min()
            else:
                minDiff = 1/dataPacket.rate
            if(gran == None or gran > minDiff):
                gran = minDiff
        return gran

    ##### REQUIRED FUNCTIONS #####
    def genSources(self):
        self.clearSourceList()
        if(self.hardwareSettings['deviceName'] in self.getDeviceList()):
            device = nidaqmx.system.Device(self.hardwareSettings['deviceName'])
            for chan in device.ai_physical_chans:
                self.Add_AISource(chan.name, -10, 10, 0.1)
            for chan in device.ao_physical_chans:
                self.Add_AOSource(chan.name, -10, 10, 0.1)
            for chan in device.di_lines:
                self.Add_DISource(chan.name, trigger=True)
            #for chan in device.do_lines:                                   #This is duplicating the di_lines!!!
            #    self.Add_DOSource(chan.name)
        else:
            self.hM.configModified(self)

    def getDeviceList(self):
        system = nidaqmx.system.System.local()
        deviceList = list()
        for device in system.devices:
            deviceList.append(device.name)

        return deviceList

    def initHardwareWorker(self):
        self.hardwareWorker = NI_DAQmxHardwareWorker()

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
            self.hardwareWorker.outQueues['command'].put(hwm(action='config'))
            self.hardwareWorker.outQueues['command'].put(hwm(action='program'))

    def onRun(self):
        self.hardwareWorker.outQueues['command'].put(hwm(action='run'))

class NI_DAQmxHardwareWorker(hardwareWorker):
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
        if(self.initialized is False and msgIn.action in ('readyCheck', 'run', 'arm', 'program', 'configure')):
            queueOut.put(hwm(action=response, msg='Hardware Not Initialized', data=False))
            return
        if(msgIn.action == 'readyCheck'):
            queueOut.put(hwm(action='readyCheck', msg='Hardware Ready!', data=True))
            return


        ##### INITILIAZATION
        if(msgIn.action == 'init'):
            queueOut.put(hwm(action='textUpdate', msg='Initializing..'))
            self.initialized = True
            self.configured = False
            self.programmed = False
            self.armed = False
            queueOut.put(hwm(action='textUpdate', msg='Done! Ready for Configuration..'))

        #### CONFIGURING
        if(msgIn.action == 'config'):
            queueOut.put(hwm(action='textUpdate', msg='Configuring..'))
            self.configured = True
            self.programmed = False
            self.armed = False
            queueOut.put(hwm(action='textUpdate', msg='Done! Ready for Waveform Programming..'))

        ##### PROGRAMMING
        if(msgIn.action == 'program'):
            queueOut.put(hwm(action='textUpdate', msg='Writing Program to Card..'))
            self.programmed = True
            self.armed = False
            queueOut.put(hwm(action='textUpdate', msg='Done! Ready for Trigger Arming..'))

        ##### ARM
        if(msgIn.action == 'arm'):
            queueOut.put(hwm(action='textUpdate', msg='Writing Program to Card..'))
            self.armed = True
            queueOut.put(hwm(action='textUpdate', msg='Done! DAQ is Armed and Ready!'))

        ##### RUN
        if(msgIn.action == 'run'):
            queueOut.put(hwm(action='textUpdate', msg='Running!', data=False))