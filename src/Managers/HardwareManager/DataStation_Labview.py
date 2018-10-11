from ctypes import *
import os

class DataStation_LabviewExtension():
    def __init__(self, ds):
        self.ds = ds
        self.devices = dict()
        self.devices['NI-FGEN'] = list()
        self.devices['NI-SCOPE'] = list()
        self.devices['NI-DMM'] = list()
        self.devices['NI-SWITCH'] = list()
        self.devices['NI-HSDIO'] = list()
        self.devices['NI-RFSA'] = list()
        self.devices['NI-RFSG'] = list()
        self.devices['NI-DCPOWER'] = list()
        #try:
        #    self.DataStation_Labview = cdll.LoadLibrary(os.path.join(self.ds.rootDir, "inc\DataStation_Labview.dll"))

        #    self.dllGetDeviceCount = self.DataStation_Labview.GetDeviceCount
        #    self.dllGetDeviceCount.argtypes = [c_char_p]
        #    self.dllGetDeviceCount.restype = c_int

        #    self.dllGetDeviceParam = self.DataStation_Labview.GetDeviceParam

        #    self.devices['NI-FGEN'] = self.getDevices('NI-FGEN')
        #    self.devices['NI-SCOPE'] = self.getDevices('NI-SCOPE')
        #    self.devices['NI-DMM'] = self.getDevices('NI-DMM')
        #    self.devices['NI-SWITCH'] = self.getDevices('NI-SWITCH')
        #    self.devices['NI-HSDIO'] = self.getDevices('NI-HSDIO')
        #    self.devices['NI-RFSA'] = self.getDevices('NI-RFSA')
        #    self.devices['NI-RFSG'] = self.getDevices('NI-RFSG')
        #    self.devices['NI-DCPOWER'] = self.getDevices('NI-DCPOWER')
        #except:
        #    print('ERROR')

    def getDeviceCount(self, driver):
        driverString = c_char_p(bytes(driver, 'utf-8'))
        return self.dllGetDeviceCount(driverString)

    def getDeviceParam(self, driver, param, deviceNo):
        driverString = c_char_p(bytes(driver, 'utf-8'))
        paramString = c_char_p(bytes(param, 'utf-8'))
        deviceNoInt = c_int(deviceNo)
        resultString = create_string_buffer(200)
        resultInt = c_int(0)

        self.dllGetDeviceParam(driverString, paramString, deviceNoInt, byref(resultString), byref(resultInt))
        return str(resultString.raw, 'utf-8').rstrip('\x00')

    def getDeviceParameters(self, driver, deviceNo):
        params = dict()
        params['Device Name'] = self.getDeviceParam(driver, 'Device Name', deviceNo)
        params['Device Model'] = self.getDeviceParam(driver, 'Device Model', deviceNo)
        params['Serial Number'] = self.getDeviceParam(driver, 'Serial Number', deviceNo)

        return params

    def getDevices(self, driver):
        devices = list()
        for i in range(0, self.getDeviceCount(driver)):
            devices.append(self.getDeviceParameters(driver, i))

        return devices
