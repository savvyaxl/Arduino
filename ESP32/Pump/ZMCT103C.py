import time
import math
from machine import ADC, Pin

# Configure ADC on GPIO 1
analog_pin = Pin(1, Pin.IN)
adc = ADC(analog_pin)

# Configure for full 3.3V range (12-bit resolution: 0 - 4095)
adc.atten(ADC.ATTN_11DB)
adc.width(ADC.WIDTH_12BIT)

# Calibration factor - adjust this to match your real multimeter readings
CALIBRATION_FACTOR = 0.063  

# Set your local mains frequency time window (200ms covers 10-12 full cycles)
SAMPLE_WINDOW_MS = 200  

print("Initializing ZMCT103C AC Current Sensor...")

while True:
    start_time = time.ticks_ms()
    sample_count = 0
    squared_sum = 0.0

    # Rapidly sample the waveform over the defined time window
    while time.ticks_diff(time.ticks_ms(), start_time) < SAMPLE_WINDOW_MS:
        raw_value = adc.read()
        
        # Convert raw 12-bit ADC value to voltage (0V to 3.3V)
        voltage = (raw_value / 4095.0) * 3.3
        
        # Subtract the DC offset bias (~1.65V when powered by 3.3V)
        ac_voltage = voltage - 1.65
        
        # Accumulate the squared values for RMS calculation
        squared_sum += (ac_voltage * ac_voltage)
        sample_count += 1

    if sample_count > 0:
        # Calculate the Root Mean Square (RMS) voltage of the waveform
        rms_voltage = math.sqrt(squared_sum / sample_count)
        
        # Convert measured voltage to RMS current in Amperes
        rms_current = rms_voltage / CALIBRATION_FACTOR
        
        # Noise gate: filter out small baseline ambient electrical noise
        if rms_current < 0.05:
            rms_current = 0.0
            
        print("RMS Current: {:.3f} A".format(rms_current))
    
    # Wait 800 milliseconds before the next reading
    time.sleep_ms(800)
