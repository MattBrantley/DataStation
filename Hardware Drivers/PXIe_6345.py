from src.Managers.HardwareManager.HardwareDevice import HardwareDevice
from src.Managers.InstrumentManager.Sockets import *
import nidaqmx, time, numpy as np, collections
from src.Managers.HardwareManager.PacketCommands import *
from src.Managers.HardwareManager.PacketMeasurements import *
from time import sleep

ms = lambda: int(round(time.time() * 1000))

class PXIe_6345(HardwareDevice):
    hardwareType = 'PXIe_6345'
    hardwareIdentifier = 'MRB_PXIe6345'
    hardwareVersion = '1.0'
    hardwareCreator = 'Matthew R. Brantley & Ian G. M. Anthony'
    hardwareVersionDate = '6/10/2019'

############################################################################################
##################################### MANDATORY FUNCS ######################################
    def scan(self):
        self.system = nidaqmx.system.System.local()
        for device in self.system.devices:
            self.Add_Device(device.name)

        self.Add_Trigger_Mode('Software')
        self.scanned.emit()

    def initialize(self, deviceName, triggerMode):
        self.device = None
        self.task = None
        self.trig_list = {}
        self.ai_sources = {}
        self.ao_sources = {}
        self.do_sources = {}
        self.device = nidaqmx.system.Device(deviceName)
        self.used_sources = []

        try:
            if(self.device is not None):
                for ai_chan in self.device.ai_physical_chans:
                    newSource = self.Add_AISource(ai_chan.name, self.device.ai_voltage_rngs[-1], self.device.ai_voltage_rngs[-2], 0.1)
                    self.ai_sources[ai_chan.name] = newSource
        except:
            pass

        self.initialized.emit()

    def configure(self):
        self.configured.emit()

    def program(self, programmingPackets):
        # self.clockSpeed = 350000 
        self.clockSpeed = 5000

        self.Set_Ready_Status(False)
        if self.task is not None:
            self.task.close()
        self.task = nidaqmx.Task()
        self.outStream = self.task.out_stream

        self.progChannels, self.progData = self.parseProgrammingPacketsWaveform(programmingPackets, self.clockSpeed)

        for progChannel in self.progChannels:
            self.task.ai_channels.add_ai_voltage_chan(progChannel, terminal_config=nidaqmx.constants.TerminalConfiguration.DIFFERENTIAL)


        triggerMode = self.Get_Trigger_Mode()
        if(triggerMode == 'Software'):
            pass
        elif(triggerMode[0:7] == 'Digital'):
            if self.task.devices:
                self.task.triggers.start_trigger.cfg_dig_edge_start_trig(self.trig_list[triggerMode].Get_Name())

        self.task.register_done_event(self.finished_callback)

        if self.task.devices:
            self.task.timing.samp_clk_rate = self.clockSpeed
            self.task.timing.samp_timing_type = nidaqmx.constants.SampleTimingType.SAMPLE_CLOCK
            self.task.timing.samp_quant_samp_mode = nidaqmx.constants.AcquisitionType.FINITE 
            self.task.timing.cfg_samp_clk_timing(self.clockSpeed)
            # self.task.read()


        self.Set_Ready_Status(True)
        self.programmed.emit()

    def softTrigger(self):
        self.Set_Ready_Status(False)
        if self.task is not None:
            sleep(0.05)
            self.task.start()
        
        self.softTriggered.emit()

    def shutdown(self):
        if self.task is not None:
            self.task.close()

    def idle(self):
        pass
        
    def stop(self):
        self.Send_Status_Message('Sending Stop Command...')
        if(hasattr(self, 'task')):
            if(self.task is not None):
                try:
                    self.task.close()
                except:
                    pass

############################################################################################
###################################### INTERNAL FUNCS ######################################

    def finished_callback(self, task_handle, status, callback_data):
        data = self.task.read()

        for i in range(0, len(data)):
            mPack = measurementPacket()
            measurement = AnalogWaveformMeasurement(0, 0, data[i])
            mPack.Add_Measurement(measurement)
            self.Push_Measurements_Packet(self.used_sources[i], mPack)

        self.Send_Status_Message('Finished!')
        self.Set_Ready_Status(True)
        self.task.stop()
        return 0

    def parseProgrammingPacketsWaveform(self, programmingPackets, clockRate):
        self.progChannels = []
        self.used_sources = []
        self.progData = None
        self.numChannels = len(programmingPackets)
        
        if(programmingPackets):
            for programData in programmingPackets:
                if(programData['programmingPacket'] is not None):
                    for cmd in programData['programmingPacket'].Get_Commands(commandType=AnalogAcquisitionCommand):
                        self.progChannels.append(programData['source'].Get_Connector_ID())
                        self.used_sources.append(programData['source'])


        self.progChannels = self.progChannels
        self.used_sources = list(self.used_sources)

        return self.progChannels, self.progData
