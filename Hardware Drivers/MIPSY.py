from Managers.HardwareManager.Hardware_Object import Hardware_Object, hardwareWorker, hwm
from PyQt5.Qt import *
from Managers.HardwareManager.Sources import *
import os, traceback, sys, glob, serial, re
import numpy as np
import nidaqmx.system
from multiprocessing import Process, Queue, Pipe

class Hardware_Driver(Hardware_Object):
    hardwareType = 'MIPSY'
    hardwareIdentifier = 'MIPSY_MRB'
    hardwareVersion = '1.0'
    hardwareCreator = 'Matthew R. Brantley'
    hardwareVersionDate = '8/12/2018'

    ##### SUPPORT FUNCTIONS #####

    def updateTableClockIndex(self, index):
            self.hardwareSettings['tableClockIndex'] = index

    def updateTableClock(self, rate):
            self.hardwareSettings['tableClockSpeed'] = int(rate)

    def getPorts(self):
        """ Lists serial port names

            :raises EnvironmentError:
                On unsupported or unknown platforms
            :returns:
                A list of the serial ports available on the system
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result

    def genSources(self):
        print('GENERATING SOURCES: ' + self.hardwareSettings['deviceName'])
        self.clearSourceList()
        if(self.hardwareSettings['deviceName'] != ''):
            with serial.Serial(self.hardwareSettings['deviceName'], 115200, timeout=1) as ser:
                ser.write(b'GCHAN,DCB\r\n')
                response = ser.readline()
                if(response is not None):
                    numDCB = self.MIPSYResponseToInt(response)
                else:
                    numDCB = 0
                self.forceNoUpdatesOnSourceAdd(True) #FOR SPEED!
                for channel in range(numDCB):
                    chOut = str(channel+1)
                    nameTemp = self.hardwareSettings['deviceName'] + '/CH' + chOut
                    ser.write(b'GDCMIN,' + chOut.encode('ascii') + b'\r\n')
                    minTemp = self.MIPSYResponseToFloat(ser.readline())
                    ser.write(b'GDCMAX,' + chOut.encode('ascii') + b'\r\n')
                    maxTemp = self.MIPSYResponseToFloat(ser.readline())
                    source = AOSource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, minTemp, maxTemp, 0.1, chOut)
                    self.addSource(source)

                self.forceNoUpdatesOnSourceAdd(False) #Have to turn it off or things go awry!

    def MIPSYResponseToInt(self, bytes):
        return int(bytes[1:-2].decode("utf-8"))

    def MIPSYResponseToFloat(self, bytes):
        return float(bytes[1:-2].decode("utf-8"))

    def parseProgramData(self, programDataList):
        for programData in programDataList:
            print('NEW PACKET:')
            print(programData.physicalConnectorID)
            print(programData.waveformData)
            print(self.waveformToClockCount(programData.waveformData))

    def waveformToClockCount(self, waveform):
        waveOut = np.copy(waveform)
        waveOut[:,0] = np.vectorize(self.getClockCountAtTimePoint)(waveform[:,0])
        return waveOut

    def getClockCountAtTimePoint(self, time):
        #time is in seconds (s)
        freq = int(self.hardwareSettings['tableClockSpeed'])
        return float(int(freq*time))

    def updateDevice(self, text):
        self.hardwareSettings['deviceName'] = text
        self.hardwareSettings['name'] = self.hardwareSettings['deviceName']
        self.genSources()

    ##### REQUIRED FUNCTINONS #####

    def initHardwareWorker(self):
        self.hardwareWorker = MIPSYHardwareWorker()

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
        for item in self.getPorts():
            index = index + 1
            deviceSelection.addItem(item)
            if(item == recoverDeviceTemp):
                deviceSelection.setCurrentIndex(index)

        #Doing this after solved the issue of rebuilding the instrument every time widget was shown
        deviceSelection.currentTextChanged.connect(self.updateDevice)

        tableClockSelection = QComboBox()
        tableClockSelection.addItem('48000000')
        tableClockSelection.addItem('10500000')
        tableClockSelection.addItem('2625000')
        tableClockSelection.addItem('656250')
        tableClockSelection.currentIndexChanged.connect(self.updateTableClockIndex)
        tableClockSelection.currentTextChanged.connect(self.updateTableClock)

        tableClockSelection.setCurrentIndex(self.hardwareSettings['tableClockIndex'])

        layout.addRow("Device:", deviceSelection)
        layout.addRow("Table Clock:", tableClockSelection)

        return hardwareConfig

    def onCreation(self):
        self.hardwareSettings['deviceName'] = ''
        self.hardwareSettings['tableClockIndex'] = 0

    def onLoad(self, loadPacket):
        pass

    def onInitialize(self):
        self.genSources()

    def onProgram(self):
        pass
        #print('I would program now')

    def onRun(self):
        self.program()
        self.hardwareWorker.outQueues['command'].put(hwm(action='run'))


class MIPSYHardwareWorker(hardwareWorker):
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
