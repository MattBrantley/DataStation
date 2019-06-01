import nidaqmx
system = nidaqmx.system.System.local()
for device in system.devices:
    print(' ')
    print(device.name)
    print(type(device.name))
    if type(device.name) == str:
        print('okay')
    print('--------')
    print(device.ai_voltage_rngs)
    print(device.ai_voltage_rngs[-1])
    print(device.ai_voltage_rngs[-2])
    for ai_chan in device.ai_physical_chans:
        print(ai_chan.name)
        
    for ao_chan in device.ao_physical_chans:
        print(ao_chan.name)

    for do_chan in device.do_lines:
        print(do_chan.name)