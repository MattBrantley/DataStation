import nifgen, numpy as np, scipy.signal, time
# Tested using nifgen v 1.0.0 (highest version number found using pip)

with nifgen.Session('ARB') as session:
    print('Starting')
    session.abort()
    session.clear_arb_memory()

    session.output_mode = nifgen.OutputMode.ARB
    session.arb_sample_rate = 100000

    print('Arb sample rate set to: ' + str(session.arb_sample_rate))

    # Generating a chirp waveform +/- 0.5v from 100-1000 Hz for 50ms
    times = np.arange(0, 0.001, 1/session.arb_sample_rate)
    #wave = scipy.signal.chirp(times, 1, times[-1], 1)
    #wave = np.multiply(wave, 0.5)
    #wave = np.append(wave, np.flip(wave, 0))
    wave = np.random.rand(12)
    print(wave)

    print('Generated chirp waveform for length: ' + str(wave.shape[0]))
    

    wfm = session.channels[0].create_waveform(wave)
    print('Creating waveform, should be (length/rate) seconds long: ' + str(wave.shape[0]/session.arb_sample_rate))
    session.trigger_mode = nifgen.TriggerMode.SINGLE
    #session.start_trigger_type = nifgen.StartTriggerType.TRIG_NONE
    session.channels[0].configure_arb_waveform(wfm, 1, 0.0)
    print('Configured arb waveform on card, gain = 1 and offset = 0.0')
    
    print('Initializing arb')
    with session.initiate():
        time.sleep(1) #sleeping longer than necessary

    print('Finished! Was the observed waveform the correct length?')