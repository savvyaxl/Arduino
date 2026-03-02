from machine import Pin, ADC # pyright: ignore[reportMissingImports]
import time

# --- CONFIGURATION ---
RELAY_PIN = 5           # Pin connected to MOSFET Gate
ADC_PIN = 34            # Pin connected to Voltage Divider
R_LOAD = 10.0           # Resistance of your load (e.g., 10 Ohms)
V_DIVIDER_RATIO = 5.55  # If using 10k and 2.2k resistors ( (10+2.2)/2.2 )
CUTOFF_VOLTAGE = 10.5   # Safety limit for Lead-Acid

# --- SETUP ---
load = Pin(RELAY_PIN, Pin.OUT)
adc = ADC(Pin(ADC_PIN))
# ESP32 ADC: 11dB attenuation allows reading up to ~3.6V
adc.atten(ADC.ATTN_11DB) 

capacity_ah = 0.0
is_testing = True

print("Starting Battery Capacity Test...")
load.value(1)  # Turn on the load

try:
    while is_testing:
        # 1. Read Raw Voltage (Average 10 readings for stability)
        raw_sum = 0
        for _ in range(10):
            raw_sum += adc.read_uv() # Returns microvolts (better accuracy)
            time.sleep(0.01)
        
        # Convert microvolts to Volts (dividing by 1,000,000)
        v_pin = (raw_sum / 10) / 1000000
        
        # 2. Calculate Actual Battery Voltage
        v_battery = v_pin * V_DIVIDER_RATIO
        
        # 3. Calculate Current (I = V / R)
        current_amps = v_battery / R_LOAD
        
        # 4. Accumulate Ah (Test runs every 1 second)
        # 1 second is 1/3600 of an hour
        capacity_ah += (current_amps / 3600)
        
        print("V: {:.2f}V | I: {:.2f}A | Ah: {:.4f}".format(v_battery, current_amps, capacity_ah))
        
        # 5. Check Cutoff
        if v_battery <= CUTOFF_VOLTAGE:
            load.value(0) # SHUT DOWN
            is_testing = False
            print("--- TEST COMPLETE ---")
            print("Final Capacity: {:.3f} Ah".format(capacity_ah))
            
        time.sleep(1) # Run every second

except KeyboardInterrupt:
    load.value(0)
    print("Test Stopped by User")
