from src.Managers.HardwareManager.HardwareDevice import HardwareDevice
from src.Managers.HardwareManager.PacketCommands import *
from src.Managers.HardwareManager.PacketMeasurements import *
from scipy import signal
import numpy as np
import time, sys, glob, serial, re, numpy as np

class Test_Driver(HardwareDevice):
    hardwareType = 'Test Driver'
    hardwareIdentifier = 'MRB_Test_Driver'
    hardwareVersion = '1.0'
    hardwareCreator = 'Matthew R. Brantley'
    hardwareVersionDate = '8/20/2018'

############################################################################################
##################################### MANDATORY FUNCS ######################################
    def scan(self):
        self.Add_Device('TEST')
        self.scanned.emit()

    def initialize(self, deviceName, triggerMode):
        self.triggered = False

        try:
            if(deviceName != ''):
                self.source0 = self.Add_AISource('AI/1', -10, 10, 0.01)
                self.Add_AISource('AI/2', -10, 10, 0.01)
                self.Add_AISource('AI/3', -10, 10, 0.01)
                self.Add_AISource('AI/4', -10, 10, 0.01)

                self.Add_AOSource('AO/1', -10, 10, 0.01)
                self.Add_AOSource('AO/2', -10, 10, 0.01)
                self.Add_AOSource('AO/3', -10, 10, 0.01)
                self.Add_AOSource('AO/4', -10, 10, 0.01)

                self.Add_DOSource('DIO/A')
                self.Add_DOSource('DIO/B')
                self.Add_DOSource('DIO/C')
                self.Add_DOSource('DIO/D')

                self.Add_DISource('DIO/Q')
                self.Add_DISource('DIO/R')
                self.Add_DISource('DIO/S')
                self.Add_DISource('DIO/T')
        except:
            pass

        self.initialized.emit()
        
    def configure(self):

        self.configured.emit()

    def program(self, programmingPackets):
        self.Set_Ready_Status(False)

        self.Set_Ready_Status(True)
        self.programmed.emit()

    def softTrigger(self):
        self.Set_Ready_Status(False)
        self.triggered = True
        self.softTriggered.emit()

    def idle(self):
        if(self.Ready_Status() is False and self.triggered is True):
            self.Send_Status_Message('Test Measurement Made!')
            self.triggered = False
            self.Set_Ready_Status(True)
            self.sendTestPacket()


############################################################################################
###################################### INTERNAL FUNCS ######################################

    def sendTestPacket(self):
        f = 1000000
        t = np.arange(0, 0.1-1/f, 1/f)
        x = np.sin(2 * np.pi * (f/10) * t)

        mPack = measurementPacket()
        measurement = AnalogWaveformMeasurement(0, f, x)
        mPack.Add_Measurement(measurement)
        self.Push_Measurements_Packet(self.source0, mPack)