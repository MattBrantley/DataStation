from Managers.HardwareManager.hardwareObject import hardwareObject, hardwareWorker, hwm
from PyQt5.Qt import *
from Managers.HardwareManager.Sources import *
import os, traceback, sys, glob, serial, re
import numpy as np
import nidaqmx.system
from multiprocessing import Process, Queue, Pipe

class Hardware_Driver(hardwareObject):
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
        self.program()

    def MIPSYResponseToInt(self, bytes):
        return int(bytes[1:-2].decode("utf-8"))

    def MIPSYResponseToFloat(self, bytes):
        return float(bytes[1:-2].decode("utf-8"))

    def MIPSToString(self, array):
        strOut = 'STBLDAT;'
        if(array is None):
            return None
        uniques = np.unique(array[:,0])

        for val in uniques:
            strOut += str(int(val))
            lines = array[np.where(array[:,0] == val)]
            lines = np.split(lines, lines.shape[0])

            for line in lines:
                if(line[0,2] == 0):
                    token = str(int(line[0,3]))
                else:
                    token = chr(line[0,3])
                
                strOut += (':' + token + ':' + str(round(line[0,1], 2)))
            
            strOut += ','

        strOut = strOut[:-1] + ';'
        return strOut

        
        #length = array.shape[0]

        #for i in range(0, length)

    def parseProgramData(self):
        eventData = self.getEvents()

        cD = None

        for programData in eventData:
            if(programData.waveformData is not None):
                if(programData.physicalConnectorID[:3] == 'DCB'):
                    channelTag = 0 #This lets us unsort it to know it's an integer
                    channelToken = int(programData.physicalConnectorID[4:])
                if(programData.physicalConnectorID[:3] == 'DIO'):
                    channelTag = 1 #This lets us unsort it to know it's a char
                    channelToken = ord(programData.physicalConnectorID[4:])
                data = self.waveformToClockCount(programData.waveformData)
                length = programData.waveformData.shape[0]
                channelColumns = np.zeros((length,2))
                channelColumns[:,0] = channelColumns[:,0] + channelTag
                channelColumns[:,1] = channelColumns[:,1] + channelToken

                wfm = np.hstack((data, channelColumns))

                if(cD is None):
                    cD = wfm
                else:
                    cD = np.vstack((cD, wfm))

        out = self.MIPSToString(cD)

        return out

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
        self.clearSourceList()
        if(self.hardwareSettings['deviceName'] != ''):
            with serial.Serial(self.hardwareSettings['deviceName'], 115200, timeout=1) as ser:
                ser.write(b'GCHAN,DCB\r\n')
                response = ser.readline()
                if(response is not None):
                    numDCB = self.MIPSYResponseToInt(response)
                else:
                    numDCB = 0

                for channel in range(numDCB):
                    chOut = str(channel+1)
                    nameTemp = self.hardwareSettings['deviceName'] + '/DCB/CH' + chOut
                    ser.write(b'GDCMIN,' + chOut.encode('ascii') + b'\r\n')
                    minTemp = self.MIPSYResponseToFloat(ser.readline())
                    ser.write(b'GDCMAX,' + chOut.encode('ascii') + b'\r\n')
                    maxTemp = self.MIPSYResponseToFloat(ser.readline())
                    source = AOSource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, minTemp, maxTemp, 0.1, 'DCB/'+chOut)
                    self.addSource(source)

                # MIPS has no way to poll Digital Out and Digital In channel counts seperately
                nameTemp = self.hardwareSettings['deviceName'] + '/DIO/A'
                source = DOSource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, 'DIO/A')
                self.addSource(source)
                nameTemp = self.hardwareSettings['deviceName'] + '/DIO/B'
                source = DOSource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, 'DIO/B')
                self.addSource(source)
                nameTemp = self.hardwareSettings['deviceName'] + '/DIO/C'
                source = DOSource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, 'DIO/C')
                self.addSource(source)
                nameTemp = self.hardwareSettings['deviceName'] + '/DIO/D'
                source = DOSource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, 'DIO/D')
                self.addSource(source)
                nameTemp = self.hardwareSettings['deviceName'] + '/DIO/E'
                source = DOSource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, 'DIO/E')
                self.addSource(source)
                nameTemp = self.hardwareSettings['deviceName'] + '/DIO/F'
                source = DOSource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, 'DIO/F')
                self.addSource(source)
                nameTemp = self.hardwareSettings['deviceName'] + '/DIO/G'
                source = DOSource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, 'DIO/G')
                self.addSource(source)
                nameTemp = self.hardwareSettings['deviceName'] + '/DIO/H'
                source = DOSource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, 'DIO/H')
                self.addSource(source)
                nameTemp = self.hardwareSettings['deviceName'] + '/DIO/I'
                source = DOSource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, 'DIO/I')
                self.addSource(source)
                nameTemp = self.hardwareSettings['deviceName'] + '/DIO/J'
                source = DOSource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, 'DIO/J')
                self.addSource(source)
                nameTemp = self.hardwareSettings['deviceName'] + '/DIO/K'
                source = DOSource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, 'DIO/K')
                self.addSource(source)
                nameTemp = self.hardwareSettings['deviceName'] + '/DIO/L'
                source = DOSource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, 'DIO/L')
                self.addSource(source)
                nameTemp = self.hardwareSettings['deviceName'] + '/DIO/M'
                source = DOSource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, 'DIO/M')
                self.addSource(source)
                nameTemp = self.hardwareSettings['deviceName'] + '/DIO/N'
                source = DOSource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, 'DIO/N')
                self.addSource(source)
                nameTemp = self.hardwareSettings['deviceName'] + '/DIO/O'
                source = DOSource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, 'DIO/O')
                self.addSource(source)
                nameTemp = self.hardwareSettings['deviceName'] + '/DIO/P'
                source = DOSource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, 'DIO/P')
                self.addSource(source)


                nameTemp = self.hardwareSettings['deviceName'] + '/DIO/Q'
                source = DISource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, 'DIO/Q')
                self.addSource(source)
                nameTemp = self.hardwareSettings['deviceName'] + '/DIO/R'
                source = DISource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, 'DIO/R', trigger=True)
                self.addSource(source)
                nameTemp = self.hardwareSettings['deviceName'] + '/DIO/S'
                source = DISource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, 'DIO/S')
                self.addSource(source)
                nameTemp = self.hardwareSettings['deviceName'] + '/DIO/T'
                source = DISource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, 'DIO/T')
                self.addSource(source)
                nameTemp = self.hardwareSettings['deviceName'] + '/DIO/U'
                source = DISource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, 'DIO/U')
                self.addSource(source)
                nameTemp = self.hardwareSettings['deviceName'] + '/DIO/V'
                source = DISource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, 'DIO/V')
                self.addSource(source)
                nameTemp = self.hardwareSettings['deviceName'] + '/DIO/W'
                source = DISource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, 'DIO/W')
                self.addSource(source)
                nameTemp = self.hardwareSettings['deviceName'] + '/DIO/X'
                source = DISource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, 'DIO/X')
                self.addSource(source)

                '''
                ser.write(b'GCHAN,DIO\r\n')
                response = ser.readline()
                if(response is not None):
                    numDCB = self.MIPSYResponseToInt(response)
                else:
                    numDCB = 0
                self.forceNoUpdatesOnSourceAdd(True) #FOR SPEED!
                for channel in range(numDCB):
                    charChannel = chr((ord('a') + channel) % 123).upper()
                    #print('--------------' + charChannel + ':')
                    stringSer = b'SDIO,' + charChannel.encode('utf-8') + b',0\r\n'
                    #print(stringSer.decode('utf-8'))
                    ser.write(b'SDIO,' + charChannel.encode('utf-8') + b',0\r\n')
                    response = ser.readline()
                    if(response is not None):
                        print(response)
                    else:
                        print('no response')

                    nameTemp = self.hardwareSettings['deviceName'] + '/DO/' + charChannel
                    source = DOSource(self, '['+self.hardwareSettings['deviceName']+'] '+nameTemp, 'DO/'+charChannel)
                    self.addSource(source)
                '''


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
