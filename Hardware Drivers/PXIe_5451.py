from src.Managers.HardwareManager.HardwareDevice import HardwareDevice
import nifgen, time, numpy as np
from src.Managers.HardwareManager.PacketCommands import *

ms = lambda: int(round(time.time() * 1000))

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
                self.Add_Device(device['Device Name'])
        self.scanned.emit()

    def initialize(self, deviceName, triggerMode):
        try:
            if(deviceName != ''):
                self.session = None
                self.wfm_handles = list()
                self.reportTime = ms()
                with nifgen.Session(deviceName) as session:
                    self.maxRate = session.arb_sample_rate
                    for i in range(0, 2):
                        self.Add_AOSource(str(i), 1, 1, 0.1)

                self.session = nifgen.Session(deviceName)
        except:
            pass

        self.initialized.emit()

    def configure(self):
        
        self.configured.emit()

    def program(self, programmingPackets):
        self.Set_Ready_Status(False)
        if(programmingPackets):
            self.session.abort()
            self.session.clear_arb_memory()
            self.wfm_handles = list()

            t0, f, wave = self.parsePacket(programmingPackets)
            if t0 is not None:
                self.session.output_mode = nifgen.OutputMode.ARB
                self.session.arb_sample_rate = f
                self.session.channels[0].wait_value = 0
                self.session.wait_behavior = nifgen.WaitBehavior.JUMP_TO

                self.wfm = self.session.channels[0].create_waveform(wave)
                self.session.trigger_mode = nifgen.TriggerMode.SINGLE
                self.session.start_trigger_type = nifgen.StartTriggerType.DIGITAL_EDGE
                self.session.digital_edge_start_trigger_source = 'PFI0'
                self.session.channels[0].configure_arb_waveform(self.wfm, 1, 0.0)
        
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
                    if(self.session.is_done() is False):
                        if(ms() - self.reportTime >= 500):
                            self.Send_Status_Message('Armed! Waiting for trigger...')
                            self.reportTime = ms()
                    else:
                        if(self.Ready_Status() is False):
                            self.Send_Status_Message('Triggered!')
                            self.Set_Ready_Status(True)
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

    def parsePacket(self, packet):
        fst = packet[0]
        cmd = fst['programmingPacket'].Get_Commands(commandType=AnalogWaveformCommand)
        if cmd:
            cmd = cmd[0]
            if(cmd.wave.shape[0] % 2 == 0):
                return cmd.t0, cmd.f, cmd.wave
            else:
                return cmd.t0, cmd.f, cmd.wave[:-1]
        else:
            return None, None, None