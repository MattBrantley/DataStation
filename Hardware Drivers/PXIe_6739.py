from src.Managers.HardwareManager.HardwareDevice import HardwareDevice
from src.Managers.InstrumentManager.Sockets import *
import nidaqmx, time, numpy as np, collections
from src.Managers.HardwareManager.PacketCommands import *
from src.Managers.HardwareManager.PacketMeasurements import *
from time import sleep

ms = lambda: int(round(time.time() * 1000))

class PXIe_6739(HardwareDevice):
    hardwareType = 'PXIe_6739'
    hardwareIdentifier = 'MRB_PXIe6739'
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
        self.scanned.emit()

    def initialize(self, deviceName, triggerMode):
        self.device = None
        self.task = None
        self.trig_list = {}
        self.ai_sources = {}
        self.ao_sources = {}
        self.do_sources = {}
        self.device = nidaqmx.system.Device(deviceName)

        try:
            if(self.device is not None):
                for ai_chan in self.device.ai_physical_chans:
                    newSource = self.Add_AISource(ai_chan.name, self.device.ai_voltage_rngs[-1], self.device.ai_voltage_rngs[-2], 0.1)
                    self.ai_sources[ai_chan.name] = newSource
                    
                for ao_chan in self.device.ao_physical_chans:
                    newSource = self.Add_AOSource(ao_chan.name, self.device.ao_voltage_rngs[-1], self.device.ao_voltage_rngs[-2], 0.1)
                    self.ao_sources[ao_chan.name] = newSource

                for do_chan in self.device.do_lines:
                    newSource = self.Add_DOSource(do_chan.name)
                    self.do_sources[do_chan.name] = newSource
                    self.Add_Trigger_Mode('Digital: ' + do_chan.name)
                    self.trig_list['Digital: ' + do_chan.name] = newSource
        except:
            pass

        self.initialized.emit()

    def configure(self):
        self.configured.emit()

    def program(self, programmingPackets):
        # self.clockSpeed = 350000 
        self.clockSpeed = 1000000 

        self.Set_Ready_Status(False)
        if self.task is not None:
            self.task.close()
        self.task = nidaqmx.Task()
        self.outStream = self.task.out_stream

        self.progChannels, self.progData = self.parseProgrammingPacketsWaveform(programmingPackets, self.clockSpeed)
        self.Send_Status_Message('New Progamming Data has Shape: ' + str(self.progData.shape))

        for progChannel in self.progChannels:
            self.task.ao_channels.add_ao_voltage_chan(progChannel)

        triggerMode = self.Get_Trigger_Mode()
        if(triggerMode == 'Software'):
            pass
        elif(triggerMode[0:7] == 'Digital'):
            if self.task.devices:
                self.task.triggers.start_trigger.cfg_dig_edge_start_trig(self.trig_list[triggerMode].Get_Name())

        if self.progData.ndim == 1:
            numSamps = self.progData.shape[0]
        else:
            numSamps = self.progData.shape[1]

        if self.task.devices:
            self.task.timing.samp_clk_rate = self.clockSpeed
            self.task.timing.samp_timing_type = nidaqmx.constants.SampleTimingType.SAMPLE_CLOCK
            self.task.timing.samp_quant_samp_mode = nidaqmx.constants.AcquisitionType.FINITE 
            self.task.timing.cfg_samp_clk_timing(self.clockSpeed, samps_per_chan=numSamps)
            self.task.write(self.progData)

        self.task.register_done_event(self.finished_callback)

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
        self.Send_Status_Message('Finished!')
        self.Set_Ready_Status(True)
        self.task.stop()
        return 0

    def parseProgrammingPacketsWaveform(self, programmingPackets, clockRate):
        self.progChannels = []
        self.progData = None
        self.numChannels = len(programmingPackets)
        
        if(programmingPackets):
            for programData in programmingPackets:
                if(programData['programmingPacket'] is not None):
                    for cmd in programData['programmingPacket'].Get_Commands(commandType=AnalogWaveformCommand):
                        # self.progChannels.append(programData['source'].Get_Connector_ID())
                        self.progData = self.addChannelDataWithPad(self.progData, cmd.wave, programData['source'].Get_Connector_ID())

                    for cmd in programData['programmingPacket'].Get_Commands(commandType=AnalogSparseCommand):
                        # self.progChannels.append(programData['source'].Get_Connector_ID())
                        waveData = self.formatSparseDataAnalog(cmd, clockRate)
                        self.progData = self.addChannelDataWithPad(self.progData, waveData, programData['source'].Get_Connector_ID())

        return self.progChannels, self.progData

    def formatSparseDataAnalog(self, cmd, clockRate):
        self.numPoints = math.ceil(np.max(cmd.pairs[:,0]) * clockRate)
        if self.numPoints == 0:
            self.numPoints = 1

        progData = np.full((self.numPoints+1), np.nan) #allocating the nparray

        progData[np.floor(cmd.pairs[:,0]*clockRate).astype(int)] = cmd.pairs[:,1]
        # self.progData[np.floor(cmd.pairs[:,0]*clockRate).astype(int) - 1] = cmd.pairs[:,1]
        ind = np.where(~np.isnan(progData[:]))[0]
        for i in range(0, len(ind)-1):
            progData[ind[i]:ind[i+1]] = progData[ind[i]]

        progData[ind[-1]:] = progData[ind[-1]]
        progData[:ind[0]] = progData[ind[0]]

        return progData

    def addChannelDataWithPad(self, progData, wave, channelID):
        if progData is None:
            progData = wave
        else:

            padMatrix = 1
            if progData.ndim == 1:
                padMatrix = 0

            if wave.shape[0] > progData.shape[padMatrix]:
                padCount = wave.shape[0] - progData.shape[padMatrix]
                if progData.ndim == 1:
                    padMatrix = np.full((padCount), progData[-1])
                else:
                    padMatrix = np.tile(progData[:,-1].transpose(), (1, padCount))

                progData = np.hstack((progData, padMatrix))
            elif wave.shape[0] < progData.shape[padMatrix]:
                padCount = progData.shape[padMatrix] - wave.shape[0]
                padMatrix = np.full((padCount), wave[-1])
                wave = np.hstack((wave, padMatrix))

            progData = np.vstack((progData, wave))

        if channelID in self.progChannels:
            ind = self.progChannels.index(channelID)
            progData[ind,:] = progData[-1,:]
            progData = np.delete(progData, -1, 0)
        else:
            self.progChannels.append(channelID)

        return progData