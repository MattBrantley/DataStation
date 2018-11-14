from src.Managers.HardwareManager.HardwareDevice import HardwareDevice
from src.Managers.HardwareManager.PacketCommands import *
import time, sys, glob, serial, re, numpy as np

ms = lambda: int(round(time.time() * 1000))

class MIPS(HardwareDevice):
    hardwareType = 'MIPS'
    hardwareIdentifier = 'MRB_MIPS'
    hardwareVersion = '1.0'
    hardwareCreator = 'Matthew R. Brantley'
    hardwareVersionDate = '8/20/2018'

############################################################################################
##################################### MANDATORY FUNCS ######################################
    def scan(self):
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                self.Add_Device(port)
            except (OSError, serial.SerialException):
                pass
        self.scanned.emit()

    def initialize(self, deviceName, triggerMode):
        try:
            if(deviceName != ''):
                self.reportTime = ms()
                self.runTable = False
                with serial.Serial(deviceName, 115200, timeout=1) as ser:
                    ser.write(b'GCHAN,DCB\r\n')
                    response = ser.readline()
                    if(response is not None):
                        numDCB = self.MIPSYResponseToInt(response)
                    else:
                        numDCB = 0

                    for channel in range(numDCB):
                        chOut = str(channel+1)
                        nameTemp = deviceName + '/DCB/CH' + chOut
                        ser.write(b'GDCMIN,' + chOut.encode('ascii') + b'\r\n')
                        minTemp = self.MIPSYResponseToFloat(ser.readline())
                        ser.write(b'GDCMAX,' + chOut.encode('ascii') + b'\r\n')
                        maxTemp = self.MIPSYResponseToFloat(ser.readline())
                        self.Add_AOSource('DCB/'+chOut, minTemp, maxTemp, 0.1)

                    # MIPS has no way to poll Digital Out and Digital In channel counts seperately
                    self.Add_DOSource('DIO/A')
                    self.Add_DOSource('DIO/B')
                    self.Add_DOSource('DIO/C')
                    self.Add_DOSource('DIO/D')
                    self.Add_DOSource('DIO/E')
                    self.Add_DOSource('DIO/F')
                    self.Add_DOSource('DIO/G')
                    self.Add_DOSource('DIO/H')
                    self.Add_DOSource('DIO/I')
                    self.Add_DOSource('DIO/J')
                    self.Add_DOSource('DIO/K')
                    self.Add_DOSource('DIO/L')
                    self.Add_DOSource('DIO/M')
                    self.Add_DOSource('DIO/N')
                    self.Add_DOSource('DIO/O')
                    self.Add_DOSource('DIO/P')

                    self.Add_DISource('DIO/Q')
                    self.Add_DISource('DIO/R', trigger=True)
                    self.Add_DISource('DIO/S')
                    self.Add_DISource('DIO/T')
                    self.Add_DISource('DIO/U')
                    self.Add_DISource('DIO/V')
                    self.Add_DISource('DIO/W')
                    self.Add_DISource('DIO/X')
        except:
            pass

        self.initialized.emit()
        
    def configure(self):

        self.configured.emit()

    def program(self, programmingPackets):
        self.Set_Ready_Status(False)
        with serial.Serial(self.Get_Standard_Field('deviceName'), 115200, timeout=1) as ser:
            self.Send_Status_Message(r'SENT: SMOD,LOC\r\n')
            ser.write(b'SMOD,LOC\r\n')
            self.Send_Status_Message('RECIEVED: ' + ser.readline().decode(encoding='ascii').rstrip("\n\r"))

            self.Send_Status_Message(r'SENT: STBLCLK,' + str(656250) + r'\r\n')
            ser.write(b'STBLCLK,' + str(656250).encode('ascii') + b'\r\n')
            self.Send_Status_Message('RECIEVED: ' + ser.readline().decode(encoding='ascii').rstrip("\n\r"))

            self.Send_Status_Message(r'SENT: STBLTRG,SW\r\n')
            ser.write(b'STBLTRG,SW\r\n')
            self.Send_Status_Message('RECIEVED: ' + ser.readline().decode(encoding='ascii').rstrip("\n\r"))
            
            self.Send_Status_Message(r'SENT: STBLDAT;' + self.parseProgrammingPackets(programmingPackets)+ r'\r\n')
            ser.write(b'STBLDAT;' + self.parseProgrammingPackets(programmingPackets).encode('ascii') + b'\r\n')
            self.Send_Status_Message('RECIEVED: ' + ser.readline().decode(encoding='ascii').rstrip("\n\r"))

            self.Send_Status_Message(r'SENT: SMOD,TBL\r\n')
            ser.write(b'SMOD,TBL\r\n')
            self.Send_Status_Message('RECIEVED: ' + ser.readline().decode(encoding='ascii').rstrip("\n\r"))

        self.Set_Ready_Status(True)
        self.programmed.emit()

    def softTrigger(self):
        self.Set_Ready_Status(False)
        with serial.Serial(self.Get_Standard_Field('deviceName'), 115200, timeout=1) as ser:
            self.runTable = True
            self.Send_Status_Message(r'SENT: TBLSTRT\r\n')
            ser.write(b'TBLSTRT\r\n')
            self.Send_Status_Message('RECIEVED: ' + ser.readline().decode(encoding='ascii').rstrip("\n\r"))
        
        self.softTriggered.emit()

    def idle(self):
        if(self.runTable is False):
            return
        with serial.Serial(self.Get_Standard_Field('deviceName'), 115200, timeout=0.1) as ser:
            responses = ser.readlines()
            for response in responses:
                response = response.decode(encoding='ascii').rstrip("\n\r")
                if(response == 'TBLCMPLT'):
                    self.Send_Status_Message('RECIEVED: Table Completed')
                    self.Set_Ready_Status(True)
                    self.runTable = False
                elif(response == 'TBLRDY'):
                    self.Send_Status_Message('RECIEVED: Table Ready!')
                    self.Set_Ready_Status(True)
                    self.runTable = False
            if(self.Ready_Status() is False):
                if(ms() - self.reportTime >= 500):
                    self.Send_Status_Message('Running...')
                    self.reportTime = ms()

############################################################################################
###################################### INTERNAL FUNCS ######################################

    def parseProgrammingPackets(self, programmingPackets):
        cD = None

        for programData in programmingPackets:
            if(programData['programmingPacket'] is not None):
                if(programData['source'].Get_Connector_ID()[:3] == 'DCB'):
                    channelTag = 0 #This lets us unsort it to know it's an integer
                    channelToken = int(programData['source'].Get_Connector_ID()[4:])
                if(programData['source'].Get_Connector_ID()[:3] == 'DIO'):
                    channelTag = 1 #This lets us unsort it to know it's a char
                    channelToken = ord(programData['source'].Get_Connector_ID()[4:])

                dataAdded = list()

                for cmd in programData['programmingPacket'].Get_Commands(commandType=AnalogSparseCommand):
                    dataAdded.append(cmd.pairs)
                for cmd in programData['programmingPacket'].Get_Commands(commandType=DigitalSparseCommand):
                    dataAdded.append(cmd.pairs)

                if(dataAdded):
                    sparseData = np.vstack(dataAdded)

                    data = self.waveformToClockCount(sparseData)
                    length = sparseData.shape[0]
                    channelColumns = np.zeros((length,2))
                    channelColumns[:,0] = channelColumns[:,0] + channelTag
                    channelColumns[:,1] = channelColumns[:,1] + channelToken

                    wfm = np.hstack((data, channelColumns))

                    if(cD is None):
                        cD = wfm
                    else:
                        cD = np.vstack((cD, wfm))

        return self.MIPSToString(cD)

    def MIPSToString(self, array):
        strOut = ''
        if(array is None):
            return ''
        uniques = np.unique(array[:,0])

        for val in uniques:
            strOut += str(int(val))
            lines = array[np.where(array[:,0] == val)]
            lines = np.split(lines, lines.shape[0])

            for line in lines:
                if(line[0,2] == 0):
                    token = str(int(line[0,3]))
                else:
                    token = chr(int(line[0,3]))
                
                strOut += (':' + token + ':' + str(round(line[0,1], 2)))
            
            strOut += ','

        strOut = strOut[:-1] + ';'
        return strOut
        
    def MIPSYResponseToInt(self, bytes):
        return int(bytes[1:-2].decode("utf-8"))

    def MIPSYResponseToFloat(self, bytes):
        return float(bytes[1:-2].decode("utf-8"))

    def waveformToClockCount(self, waveform):
        waveOut = np.copy(waveform)
        waveOut[:,0] = np.vectorize(self.getClockCountAtTimePoint)(waveform[:,0])
        return waveOut

    def getClockCountAtTimePoint(self, time):
        #time is in seconds (s)
        #freq = int(self.hardwareSettings['tableClockSpeed'])
        freq = int(656250)
        return float(int(freq*time))
