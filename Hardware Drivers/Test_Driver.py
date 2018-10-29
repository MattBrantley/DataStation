from src.Managers.HardwareManager.HardwareDevice import HardwareDevice
from src.Managers.HardwareManager.PacketCommands import *
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

    def initialize(self, deviceName):
        try:
            if(deviceName != ''):
                self.Add_AISource('AI/1', -10, 10, 0.01)
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
        
        self.softTriggered.emit()

    def idle(self):
        pass
