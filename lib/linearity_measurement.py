import time
import numpy as np
from tqdm import tqdm

class LinearityMeasurement:
    def __init__(self, signal_generator, oscilloscope):
        """Initialize the LinearityMeasurement class with a signal generator and oscilloscope."""
        self.sg = signal_generator
        self.osc = oscilloscope
        
    def calculate_intercept(self, input_voltages, products):
        """Estimate the intercept point based on the input power and intermodulation products."""
        coefficients = np.polyfit(input_voltages, products, 1)  # Linear fit
        intercept = -coefficients[1] / coefficients[0]  # Calculate intercept point
        return intercept
    
    def set_oscilloscope(self, freq, amp):
        """Oscilloscope Settings for a certain frequency and amplitude"""

        # Set timebase to 1 ms/div
        self.osc.set_timebase(2/freq)

        # Set channel 1 vertical scale to 20 mV/div
        self.osc.set_channel_scale(1, amp*20)

        # Wait for command to complete
        time.sleep(0.1)

        # Set trigger level to 100 mV on channel 1
        self.osc.set_trigger_source(1)
        self.osc.set_trigger_level(0)

    def measure_iip2(self, start_voltage=1e-3, stop_voltage=1, num=10, freq1=1e6, freq2=1.01e6, fs=50e3):
        """Measure IIP2 (second-order intercept point)."""
        input_voltages = np.round(np.linspace(start_voltage, stop_voltage, num),5)
        second_order_products = []
        
        # # Oscilloscope Settings for a certain frequency and amplitude
        # self.set_oscilloscope(freq1, start_voltage)
        
        # Allow time for the instrument to configure
        time.sleep(1)

        for voltage in tqdm(input_voltages, desc="Sweeping Voltages"):
            # Set two-tone signal with specified power
            self.sg.set_waveform("SIN", frequency=freq1, amplitude=voltage, offset=0)
            self.sg.enable_output()
            
            # Oscilloscope Settings for a certain frequency and amplitude
            self.set_oscilloscope(freq1, voltage)
            print(voltage)
            
            # Oscilloscope Settings for frequency and amplitude
            time.sleep(1)
            self.osc.run()
            
            # Allow time for the instrument to configure
            time.sleep(1)          
            
            # Measure the output from the oscilloscope (assuming two-tone output capture)
            waveform_volts = self.osc.get_waveform_data(channel=1)
            time.sleep(1)
            
            # Calculate Second Order Products
            second_order_power = self.calculate_second_order_product(waveform_volts, freq1, freq2, fs)
            second_order_products.append(second_order_power)
            
            # Allow time for the instrument to configure
            time.sleep(0.1)
            self.osc.stop()
            
        self.sg.disable_output()
        
        # Check for intercept point (linear region of the fundamental vs second-order product)
        if len(second_order_products) > 1:
            second_order_intercept = self.calculate_intercept(input_voltages, second_order_products)
            print(f"IIP2 found at input power = {second_order_intercept} dBm")
        
        return input_voltages, second_order_products

    def calculate_second_order_product(self, waveform_volts, freq1, freq2, fs):
        """Calculate second-order intermodulation product from waveform."""
        # Perform FFT to find second-order intermodulation products at f1+f2 and f1-f2
        fft     = np.fft.fft(waveform_volts)
        freqs   = np.fft.fftfreq(len(waveform_volts),1/fs)
        
        # Take the absolute value to get the magnitude
        fft_magnitude = np.abs(fft[:len(fft) // 2]) / len(fft[:len(fft) // 2])
        fft_freq  = freqs[:len(fft) // 2]

        # Find the power at f1+f2 (second-order sum) and f1-f2 (second-order difference)
        f_sum = freq1 + freq2
        f_diff = np.abs(freq1 - freq2)
        # print(f"Frequencies = {f_sum, f_diff} Hz")

        # Find the indices of the corresponding frequencies
        idx_sum = np.argmin(np.abs(np.float64(fft_freq) - f_sum))
        idx_diff = np.argmin(np.abs(np.float64(fft_freq) - f_diff))
        # print(f"Indices = {idx_sum, idx_diff} Hz")

        # Calculate the power of the second-order products
        second_order_power_sum = fft_magnitude[idx_sum] ** 2
        second_order_power_diff = fft_magnitude[idx_diff] ** 2

        # Return the maximum power between f1+f2 and f1-f2, converted to dBm
        second_order_power = max(second_order_power_sum, second_order_power_diff)
        return 10 * np.log10(second_order_power)

    # Rest of the class (P1dB, IIP3, etc.)...