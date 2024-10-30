# signal_generator.py
import re
import pyvisa
from pyvisa.resources import MessageBasedResource
    
class SignalGenerator:
    def __init__(self, resource):
        self.rm = pyvisa.ResourceManager()
        self.sg: MessageBasedResource = self.rm.open_resource(resource)
        self.sg.timeout = 10000  # 10-second timeout for commands
        self.sg.write_termination = '\n'
        self.sg.read_termination = '\n'

    def idn(self):
        """Query the oscilloscope's identity"""
        return self.sg.query('*IDN?')

    def reset(self):
        """Reset the oscilloscope to factory defaults"""
        self.sg.write('*RST')
        
    def enable_output(self, channel=1):
        """Enable the output for the specified channel (1 or 2)."""
        if channel == 1:
            self.sg.write("OUTP1 ON")
        elif channel == 2:
            self.sg.write("OUTP2 ON")

    def disable_output(self, channel=1):
        """Disable the output for the specified channel (1 or 2)."""
        if channel == 1:
            self.sg.write("OUTP1 OFF")
        elif channel == 2:
            self.sg.write("OUTP2 OFF")

    def query_output_state(self):
        """Query the output state (ON or OFF)."""
        return self.sg.query("OUTPut?")

    def set_waveform(self, waveform_type="SIN", frequency=1000, amplitude=5.0, offset=0):
        """Set the waveform type, frequency (Hz), amplitude (Vpp), and offset (VDC)."""
        self.sg.write(f"APPLy:{waveform_type} {frequency},{amplitude},{offset}")
        
    def set_frequency(self, frequency):
        """Set the output frequency."""
        self.sg.write(f"FREQuency {frequency}")

    def set_amplitude(self, amplitude):
        """Set the amplitude of the signal (Vpp)."""
        self.sg.write(f"VOLTage {amplitude}")

    def set_offset(self, offset):
        """Set the DC offset of the signal (VDC)."""
        self.sg.write(f"VOLTage:OFFSet {offset}")
        
    def set_modulation(self, modulation_type="AM", source="INT", frequency=1000, depth=50):
        """Set modulation (AM, FM, PM) with internal or external source."""
        if modulation_type == "AM":
            self.sg.write(f"AM:SOUR {source}")
            self.sg.write(f"AM:INT:FREQ {frequency}")
            self.sg.write(f"AM:DEPTh {depth}")
            self.sg.write("AM:STAT ON")
        elif modulation_type == "FM":
            self.sg.write(f"FM:SOUR {source}")
            self.sg.write(f"FM:INT:FREQ {frequency}")
            self.sg.write(f"FM:DEViation {depth}")
            self.sg.write("FM:STAT ON")
        # Add more modulation options (PM, etc.) if necessary

    def turn_off_modulation(self, modulation_type="AM"):
        """Turn off modulation."""
        if modulation_type == "AM":
            self.sg.write("AM:STAT OFF")
        elif modulation_type == "FM":
            self.sg.write("FM:STAT OFF")

    def close(self):
        """Close the connection to the oscilloscope"""
        self.sg.close()
