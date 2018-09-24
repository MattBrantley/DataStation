from src.Managers.HardwareManager.HardwareDevice import HardwareDevice
import nifgen, time, numpy as np
from src.Managers.HardwareManager.PacketCommands import *

class PXIe_5451(HardwareDevice):
    hardwareType = 'NI PXIe-5451'
    hardwareIdentifier = 'MRB_PXIe5451'
    hardwareVersion = '1.0'
    hardwareCreator = 'Matthew R. Brantley'
    hardwareVersionDate = '8/20/2018'

############################################################################################
##################################### MANDATORY FUNCS ######################################
    def scan(self):
        for device in self.systemDeviceInfo['NI-FGEN']:
            if(device['Device Model'] == 'NI PXIe-5451'):
                self.addDevice(device['Device Name'])
        self.scanned.emit()

    def initialize(self, deviceName):
        if(deviceName != ''):
            with nifgen.Session(deviceName) as session:
                self.maxRate = session.arb_sample_rate
                for i in range(0, 2):
                    self.Add_AOSource(str(i), -10, 10, 0.1)
                    #self.maxRate = session.arb_sample_rate

        self.initialized.emit()

    def configure(self):
        
        self.configured.emit()

    def program(self, programmingPackets):
        self.Set_Ready_Status(False)
        if(programmingPackets):
            with nifgen.Session(self.Get_Standard_Field('deviceName')) as session:
                session.clear_arb_memory()

                t0, f, wave = self.parsePacket(programmingPackets)
                session.output_mode = nifgen.OutputMode.ARB
                session.arb_sample_rate = f
                session.wait_behavior = nifgen.WaitBehavior.JUMP_TO
                session.wait_value = 0

                wfm = session.create_waveform(wave)
                session.trigger_mode = nifgen.TriggerMode.SINGLE
                #session.start_trigger_type = nifgen.StartTriggerType.SOFTWARE_EDGE
                session.commit()
                session.configure_arb_waveform(wfm, 1, 0.0)
                with session.initiate():
                    #session.send_software_edge_trigger()
                    try:
                        session.wait_until_done(max_time=5)
                    except:
                        pass
                    #time.sleep(2)
        
        self.Set_Ready_Status(True)
        self.programmed.emit()

    def softTrigger(self):
        self.Set_Ready_Status(False)
        with nifgen.Session(self.Get_Standard_Field('deviceName')) as session:
            session.output_mode = nifgen.OutputMode.ARB
            with session.initiate():
                session.wait_until_done(max_time=10000)
        
        self.Set_Ready_Status(True)
        self.softTriggered.emit()

############################################################################################
###################################### INTERNAL FUNCS ######################################

    def parsePacket(self, packet):
        fst = packet[0]
        cmd = fst['programmingPacket'].Get_Commands(commandType=AnalogWaveformCommand)[0]
        if(cmd.wave.shape[0] % 2 == 0):
            return cmd.t0, cmd.f, cmd.wave
        else:
            return cmd.t0, cmd.f, cmd.wave[:-1]
            
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
                print('DATA PACKET')
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