from src.Managers.HardwareManager.HardwareDevice import HardwareDevice
import nidaqmx, time, numpy as np, collections
from src.Managers.HardwareManager.PacketCommands import *
from src.Managers.HardwareManager.PacketMeasurements import *

ms = lambda: int(round(time.time() * 1000))

class NI_DAQmx(HardwareDevice):
    hardwareType = 'NI_DAQmx'
    hardwareIdentifier = 'MRB_DAQmx'
    hardwareVersion = '1.0'
    hardwareCreator = 'Matthew R. Brantley & Ian G. M. Anthony'
    hardwareVersionDate = '5/28/2019'

############################################################################################
##################################### MANDATORY FUNCS ######################################
    def scan(self):
        self.system = nidaqmx.system.System.local()
        for device in self.system.devices:
            self.Add_Device(device.name)

        self.Add_Trigger_Mode('Software')
        #self.Add_Trigger_Mode('Front Digital Trigger')
        self.scanned.emit()

    def initialize(self, deviceName, triggerMode):
        self.device = None
        self.ai_sources = {}
        self.ao_sources = {}
        self.do_sources = {}
        self.device = nidaqmx.system.Device(deviceName)

        try:
            if(self.device is not None):
                for ai_chan in self.device.ai_physical_chans:
                    newSource = self.Add_AISource(ai_chan.name, self.device.ai_voltage_rngs[-1], self.device.ai_voltage_rngs[-2], 0.1)
                    self.ai_sources[ai_chan.name] = newSource
                    #self.ai_sources.append(newSource)
                    
                for ao_chan in self.device.ao_physical_chans:
                    newSource = self.Add_AOSource(ao_chan.name, self.device.ao_voltage_rngs[-1], self.device.ao_voltage_rngs[-2], 0.1)
                    self.ao_sources[ao_chan.name] = newSource
                    #self.ao_sources.append(newSource)

                for do_chan in self.device.do_lines:
                    newSource = self.ADD_DOSource(do_chan.name)
                    self.do_sources[do_chan.name] = newSource
                    #self.do_sources.append(newSource)
        except:
            pass

        self.initialized.emit()

    def configure(self):
        
        self.configured.emit()

    def program(self, programmingPackets):
        self.Set_Ready_Status(False)
        if(programmingPackets):
            for programData in programmingPackets:
                if(programData['programmingPacket'] is not None):
                    connectorID = programData['source'].Get_Connector_ID()
                    deviceChannel = self.ao_sources[connectorID]
                    for cmd in programData['programmingPacket'].Get_Commends(commandType=AnalogSparseCommand):
                        

        # self.Set_Ready_Status(False)
        # if(programmingPackets):
        #     packet = programmingPackets[0]['programmingPacket'].Get_Commands(commandType=AnalogAcquisitionCommand)
        #     if packet:
        #         packet = packet[0]
        #         if(packet is not None):
        #             self.session.abort()
        #             self.session.vertical_range = packet.acqMax-packet.acqMin
        #             self.session.vertical_coupling = niscope.VerticalCoupling.AC
        #             self.session.vertical_offset = (packet.acqMin + packet.acqMax) / 2
        #             self.session.probe_attenuation = 1
        #             self.session.channels[0].channel_enabled = True
        #             self.session.channels[1].channel_enabled = False
        #             self.session.channels[2].channel_enabled = False
        #             self.session.channels[3].channel_enabled = False
        #             self.session.channels[4].channel_enabled = False
        #             self.session.channels[5].channel_enabled = False
        #             self.session.channels[6].channel_enabled = False
        #             self.session.channels[7].channel_enabled = False

        #             self.session.min_sample_rate = packet.rate
        #             self.session.horz_min_num_pts = packet.noSamples
        #             self.session.horz_record_ref_position = 0
        #             self.session.horz_num_records = 1
        #             self.session.horz_enforce_realtime = True

        #             self.session.trigger_type = niscope.TriggerType.EDGE
        #             self.session.trigger_level = 1.0
        #             self.session.trigger_source = 'TRIG' 


        #             self.readArray = np.ndarray(packet.noSamples, dtype=np.float64)

        self.Set_Ready_Status(True)
        self.programmed.emit()

    def softTrigger(self):
        self.Set_Ready_Status(False)
        # self.session.initiate()
        
        self.softTriggered.emit()

    def shutdown(self):
        pass
        # if(self.session is not None):
        #     self.session.close()

    def idle(self):
        pass
        # if(hasattr(self, 'session')):
        #     if(self.session is not None):
        #         try:
        #             if(not self.booting):
        #                 if(self.session.acquisition_status() == niscope.AcquisitionStatus.COMPLETE):
        #                     if(self.Ready_Status() is False):
        #                         self.Send_Status_Message('Triggered!')
        #                         wfmInfo = self.session.channels[0].fetch_into(self.readArray)
        #                         self.writeToPacket(self.readArray, wfmInfo[0])
        #                         self.Set_Ready_Status(True)

        #                 else:
        #                     if(ms() - self.reportTime >= 500):
        #                         self.Send_Status_Message('Armed! Waiting for trigger...')
        #                         self.reportTime = ms()
        #         except:
        #             pass
        
    def stop(self):
        pass
        # self.Send_Status_Message('Sending Stop Command...')
        # if(hasattr(self, 'session')):
        #     if(self.session is not None):
        #         try:
        #             self.session.abort()
        #         except:
        #             pass

############################################################################################
###################################### INTERNAL FUNCS ######################################

    def writeToPacket(self, nparray, wfmInfo):
        mPack = measurementPacket()
        measurement = AnalogWaveformMeasurement(wfmInfo.absolute_initial_x, 1/wfmInfo.x_increment, nparray)
        mPack.Add_Measurement(measurement)
        self.Push_Measurements_Packet(self.source0, mPack)
