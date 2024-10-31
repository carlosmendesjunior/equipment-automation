# oscilloscope.py
import re
import pyvisa
from pyvisa.resources import MessageBasedResource
    
class Oscilloscope:
    def __init__(self, resource):
        self.rm = pyvisa.ResourceManager()
        self.scope: MessageBasedResource = self.rm.open_resource(resource)
        self.scope.timeout = 30000  # 30-second timeout for commands
        self.scope.write_termination = '\n'
        self.scope.read_termination = '\n'

    def idn(self):
        """Query the oscilloscope's identity"""
        return self.scope.query('*IDN?')

    def reset(self):
        """Reset the oscilloscope to factory defaults"""
        self.scope.write('*RST')
        
    def run(self):
        """The :RUN command starts the oscilloscope"""
        self.scope.write(':RUN')
        
    def stop(self):
        """The :STOP command stops the oscilloscope"""
        self.scope.write(':STOP')

    def set_timebase(self, scale):
        """Set the timebase scale in seconds per division"""
        self.scope.write(f':TIMEBASE:SCALE {scale}')
       
    def set_channel_scale(self, channel=1, scale=10e-3):
        """Set the vertical scale for a specific channel"""
        if channel == 1:
            self.scope.write(f':CHANNEL1:SCALE {scale}')
        elif channel == 2:
            self.scope.write(f':CHANNEL2:SCALE {scale}')
        
    def set_source_channel(self, channel):
        """Set the channel of which the waveform data will be read"""
        self.scope.write(f':WAVeform:SOURce CHANNEL{channel}')
        
    def set_wav_mode(self, mode):
        """Set the reading mode used by :WAVeform:DATA? (NORMal, MAX, RAW)"""
        self.scope.write(f':WAVeform:MODE {mode}')
        
    def set_wav_format(self, format):
        """Set the return format of the waveform data (WORD|BYTE|ASCii)"""
        self.scope.write(f':WAVeform:FORMat {format}')
        
    def set_wav_start(self, start):
        """Set the start point of waveform data reading"""
        self.scope.write(f':WAVeform:STARt {start}')
        
    def set_wav_stop(self, stop):
        """ Set the stop point of waveform data reading."""
        self.scope.write(f':WAVeform:STOP {stop}')

    def set_trigger_level(self, level):
        """Set the trigger level in volts"""
        self.scope.write(f':TRIGGER:EDGE:LEVEL {level}')

    def set_trigger_source(self, channel):
        """Set the trigger source to a specific channel"""
        self.scope.write(f':TRIGGER:EDGE:SOURCE CHANNEL{channel}')

    def set_acquisition_mode(self, mode):
        """Set acquisition mode (e.g., NORMAL, AVERAGE, PEAK, SINGLE)"""
        self.scope.write(f':ACQUIRE:MODE {mode}')

    def trigger_single(self):
        """Trigger a single acquisition"""
        self.scope.write(':TRIGGER:SWEEP SINGLE')
        
    def get_inferred_sampling_frequency(self):
        """Infer the sampling frequency based on the timebase and memory depth."""
        try:
            # Query the time scale (seconds per division)
            time_scale = float(self.scope.query(":TIM:SCAL?"))  # In seconds/div

            # Assume 12 divisions on the oscilloscope display
            total_time = time_scale * 12  # Total time across the screen

            # Query the number of points captured
            num_points = int(self.scope.query(":WAV:POIN?"))

            # Calculate the sampling frequency
            sampling_freq = num_points / total_time
            # print(f"Inferred Sampling Frequency: {sampling_freq} Hz")
            return sampling_freq
        except Exception as e:
            print(f"Error inferring sampling frequency: {e}")
            return None
        
    def waveform_data(self):
        """ Read the waveform data. n"""
        return self.scope.query(':WAVeform:DATA?')
           
    def get_waveform_data(self, channel):
        """Capture waveform data from a specific channel in increments up to 24 MSa"""
        self.stop()  # Stop acquisition
        self.set_source_channel(channel)  # Set the channel to capture from
        self.set_wav_mode("NORMAL")  # Set waveform mode to NORMAL
        self.set_wav_format("ASCii")  # Set the waveform format to ASCii

        # Set the start and stop points for waveform data
        self.set_wav_start(1)  # Set start point of waveform data
        self.set_wav_stop(1.2e3)  # Set stop point of waveform data

        # Request raw binary data and read it
        rawData = self.waveform_data()  # Request the data
        
        # Wait for previous operations to complete
        self.scope.query("*OPC?")
        
        # Pre-process data
        data = re.sub(r'.', '', rawData, count = 11)
        waveForm = [float(item) for item in data.split(',')]

        return waveForm
        
    def get_header(self):
        self.scope.write(":DATA:WAVE:SCREen:HEAD?")  # Send command to request header
        raw_header_info = self.scope.read_raw()  # Read the raw response
        try:    # Try decoding the raw header info
            header_info = raw_header_info.decode('utf-8')  # Attempt to decode using UTF-8
        except UnicodeDecodeError:
            header_info = raw_header_info.decode('latin-1')  # Fallback to Latin-1 if UTF-8 fails
        return header_info

    def close(self):
        """Close the connection to the oscilloscope"""
        self.scope.close()
