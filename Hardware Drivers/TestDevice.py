from src.Managers.HardwareManager.HardwareDevice import HardwareDevice
import niscope

class TestDevice(HardwareDevice):
    hardwareType = 'Test Device'
    hardwareIdentifier = 'TD_Ugh'
    hardwareVersion = '1.0'
    hardwareCreator = 'Matthew R. Brantley'
    hardwareVersionDate = '8/20/2018'

    def initialize(self):
        for device in self.systemDeviceInfo['NI-SCOPE']:
            self.addDevice(device)

        self.initialized.emit()

    def device(self, deviceName):
        with niscope.Session(deviceName) as session:
            self.maxRate = session.max_real_time_sampling_rate
            for i in range(0, session.channel_count):
                self.Add_AOSource(str(i), -10, 10, 0.1)
