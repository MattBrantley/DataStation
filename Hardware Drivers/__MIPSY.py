from src.Managers.HardwareManager.hardwareObject import hardwareObject, hardwareWorker, hwm
from src.Managers.HardwareManager.Sources import *
import os, traceback, sys, glob, serial, re, numpy as np
from PyQt5.Qt import *
from multiprocessing import Process, Queue, Pipe

class Hardware_Driver(hardwareObject):
    hardwareType = 'MIPSY'
    hardwareIdentifier = 'MIPSY_MRB'
    hardwareVersion = '1.0'
    hardwareCreator = 'Matthew R. Brantley'
    hardwareVersionDate = '8/12/2018'

    ##### SUPPORT FUNCTIONS #####

    def waveformToClockCount(self, waveform):
        waveOut = np.copy(waveform)
        waveOut[:,0] = np.vectorize(self.getClockCountAtTimePoint)(waveform[:,0])
        return waveOut

    def getClockCountAtTimePoint(self, time):
        #time is in seconds (s)
        freq = int(self.hardwareSettings['tableClockSpeed'])
        return float(int(freq*time))

    def prepareConfigData(self):
        configs = dict()
        configs['ch'] = self.hardwareSettings['deviceName']
        configs['tableClockSpeed'] = self.hardwareSettings['tableClockSpeed']
        return configs

    def prepareArmData(self):
        if(self.hardwareSettings['triggerMode'] == 'Software'):
            return 'STBLTRG,SW'
        if(self.hardwareSettings['triggerMode'] == 'Digital Rise'):
            return 'STBLTRG,POS'
        if(self.hardwareSettings['triggerMode'] == 'Digital Fall'):
            return 'STBLTRG,NEG'

    ##### REQUIRED FUNCTINONS #####

    def getDeviceList(self):
        pass

    def genSources(self):
        pass

    def initHardwareWorker(self):
        self.hardwareWorker = MIPSYHardwareWorker()

    def hardwareObjectConfigWidget(self):
        hardwareConfig = QWidget()

        layout = QFormLayout()
        hardwareConfig.setLayout(layout)

        tableClockSelection = QComboBox()
        tableClockSelection.addItem('48000000')
        tableClockSelection.addItem('10500000')
        tableClockSelection.addItem('2625000')
        tableClockSelection.addItem('656250')
        tableClockSelection.currentIndexChanged.connect(self.updateTableClockIndex)
        tableClockSelection.currentTextChanged.connect(self.updateTableClock)

        tableClockSelection.setCurrentIndex(self.hardwareSettings['tableClockIndex'])

        layout.addRow("Table Clock:", tableClockSelection)

        return hardwareConfig

    def onCreation(self):
        self.hardwareSettings['deviceName'] = ''
        self.hardwareSettings['tableClockIndex'] = 0

    def onLoad(self, loadPacket):
        pass

    def onInitialize(self):
        self.hardwareWorker.outQueues['command'].put(hwm(action='init'))
        self.genSources()
        self.triggerModes['Software'] = True
        self.triggerModes['Digital Rise'] = True
        self.triggerModes['Digital Fall'] = True
        self.hardwareSettings['tableClockSpeed'] = 48000000

    def onProgram(self):
        configData = self.prepareConfigData()
        programmingData = self.parseProgramData()
        armData = self.prepareArmData()
        if(programmingData is not None):
            self.hardwareWorker.outQueues['command'].put(hwm(action='config', data=configData))
            self.hardwareWorker.outQueues['command'].put(hwm(action='program', data=programmingData))
            self.hardwareWorker.outQueues['command'].put(hwm(action='arm', data=armData))

    def onRun(self):
        self.hardwareWorker.outQueues['command'].put(hwm(action='run'))

class MIPSYHardwareWorker(hardwareWorker):
    def __init__(self):
        self.initialized = False
        self.configured = False
        self.programmed = False
        self.armed = False
        self.ch = None
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
            if('ch' in msgIn.data):
                self.ch = msgIn.data['ch']
                with serial.Serial(self.ch, 115200, timeout=1) as ser:
                    queueOut.put(hwm(action='textUpdate', msg='Writing: \"SMOD,LOC\"'))
                    ser.write(b'SMOD,LOC\r\n')
                    queueOut.put(hwm(action='textUpdate', msg='Writing: \"STBLCLK,' + str(msgIn.data['tableClockSpeed']) + '\"'))
                    ser.write(b'STBLCLK,' + str(msgIn.data['tableClockSpeed']).encode('ascii') + b'\r\n')

            self.configured = True
            queueOut.put(hwm(action='textUpdate', msg='Done! Ready for Waveform Programming..'))

        ##### PROGRAMMING
        if(msgIn.action == 'program'):
            queueOut.put(hwm(action='textUpdate', msg='Writing Program to Card..'))
    
            if(self.ch is not None):
                with serial.Serial(self.ch, 115200, timeout=1) as ser:
                    queueOut.put(hwm(action='textUpdate', msg='Program Writing: \"' + msgIn.data + '\"'))
                    ser.write(msgIn.data.encode('ascii') + b'\r\n')

            self.programmed = True
            queueOut.put(hwm(action='textUpdate', msg='Done! Ready for Trigger Arming..'))

        ##### ARM
        if(msgIn.action == 'arm'):
            queueOut.put(hwm(action='textUpdate', msg='Arming..'))
            if(self.ch is not None):
                with serial.Serial(self.ch, 115200, timeout=1) as ser:
                    queueOut.put(hwm(action='textUpdate', msg='Writing Trigger: \"' + msgIn.data + '\"'))
                    ser.write(msgIn.data.encode('ascii') + b'\r\n')
                    queueOut.put(hwm(action='textUpdate', msg='Writing: \"SMOD,TBL\"'))
                    ser.write(b'SMOD,TBL\r\n')

            self.armed = True
            queueOut.put(hwm(action='textUpdate', msg='Done! DAQ is Armed and Ready!'))

        ##### RUN
        if(msgIn.action == 'run'):
            queueOut.put(hwm(action='textUpdate', msg='Running!', data=False))
            if(self.ch is not None):
                with serial.Serial(self.ch, 115200, timeout=1) as ser:
                    queueOut.put(hwm(action='textUpdate', msg='Writing: \"TBLSTRT\"'))
                    ser.write(b'TBLSTRT\r\n')
