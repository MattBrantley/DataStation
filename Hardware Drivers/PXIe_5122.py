from src.Managers.HardwareManager.HardwareDevice import HardwareDevice
import niscope, time, numpy as np
from src.Managers.HardwareManager.PacketCommands import *
from src.Managers.HardwareManager.PacketMeasurements import *

ms = lambda: int(round(time.time() * 1000))

class PXIe_5122(HardwareDevice):
    hardwareType = 'NI PXIe-5122'
    hardwareIdentifier = 'MRB_PXIe5122'
    hardwareVersion = '1.0'
    hardwareCreator = 'Matthew R. Brantley'
    hardwareVersionDate = '8/20/2018'

############################################################################################
##################################### MANDATORY FUNCS ######################################
    def scan(self):
        for device in self.systemDeviceInfo['NI-SCOPE']:
            if(device['Device Model'] == 'NI PXIe-5122'):
                self.Add_Device(device['Device Name'])

        self.Add_Trigger_Mode('Software')
        self.Add_Trigger_Mode('Front Digital Trigger')
        self.scanned.emit()

    def initialize(self, deviceName, triggerMode):
        try:

            if(deviceName != ''):
                self.session = None
                self.wfm_handles = list()
                self.reportTime = ms()
                with niscope.Session(deviceName) as session:
                    # Would get more session data here
                    self.source0 = self.Add_AISource('0', -10, 10, 0.1)
                    self.source1 = self.Add_AISource('1', -10, 10, 0.1)

                self.session = niscope.Session(deviceName)

            if(triggerMode == 'Front Digital Trigger'):
                self.Add_Digital_Trigger('PXIe-5122 Trigger')
        except:
            pass

        self.initialized.emit()

    def configure(self):
        
        self.configured.emit()

    def program(self, programmingPackets):
        self.Set_Ready_Status(False)
        if(programmingPackets):
            packet = programmingPackets[0]['programmingPacket'].Get_Commands(commandType=AnalogAcquisitionCommand)
            if packet:
                packet = packet[0]
                if(packet is not None):
                    self.session.abort()
                    self.session.vertical_range = packet.acqMax-packet.acqMin
                    self.session.vertical_coupling = niscope.VerticalCoupling.AC
                    self.session.vertical_offset = (packet.acqMin + packet.acqMax) / 2
                    self.session.probe_attenuation = 1
                    self.session.channels[0].channel_enabled = True
                    self.session.channels[1].channel_enabled = False

                    self.session.min_sample_rate = packet.rate
                    self.session.horz_min_num_pts = packet.noSamples
                    self.session.horz_record_ref_position = 0
                    self.session.horz_num_records = 1
                    self.session.horz_enforce_realtime = True

                    self.session.trigger_type = niscope.TriggerType.EDGE
                    self.session.trigger_level = 1.0
                    self.session.trigger_source = 'TRIG' 


                    self.readArray = np.ndarray(packet.noSamples, dtype=np.float64)


        self.Set_Ready_Status(True)
        self.programmed.emit()

    def softTrigger(self):
        self.Set_Ready_Status(False)
        self.session.initiate()
        
        self.softTriggered.emit()

    def shutdown(self):
        if(self.session is not None):
            self.session.close()

    def idle(self):
        if(hasattr(self, 'session')):
            if(self.session is not None):
                try:
                    if(self.session.acquisition_status() == niscope.AcquisitionStatus.COMPLETE):
                        if(self.Ready_Status() is False):
                            self.Send_Status_Message('Triggered!')
                            self.Set_Ready_Status(True)
                            wfmInfo = self.session.channels[0].fetch_into(self.readArray)
                            self.writeToPacket(self.readArray, wfmInfo[0])

                    else:
                        if(ms() - self.reportTime >= 500):
                            self.Send_Status_Message('Armed! Waiting for trigger...')
                            self.reportTime = ms()
                except:
                    pass
        
    def stop(self):
        self.Send_Status_Message('Sending Stop Command...')
        if(hasattr(self, 'session')):
            if(self.session is not None):
                try:
                    self.session.abort()
                except:
                    pass

############################################################################################
###################################### INTERNAL FUNCS ######################################

    def writeToPacket(self, nparray, wfmInfo):
        mPack = measurementPacket()
        measurement = AnalogWaveformMeasurement(wfmInfo.absolute_initial_x, 1/wfmInfo.x_increment, nparray)
        mPack.Add_Measurement(measurement)
        self.Push_Measurements_Packet(self.source0, mPack)
