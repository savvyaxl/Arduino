from machine import Pin, ADC
import math
import time

# --- Configuration ---
adc_pin = Pin(7, Pin.IN)
adc = ADC(adc_pin)
adc.atten(ADC.ATTN_11DB)

# --- Standard 10k NTC Thermistor Profile ---
BETA = 3950.0                 # Standard manufacturer Beta parameter for 10k NTC
ROOM_TEMP_KELVIN = 298.15     # 25°C in Kelvin
NOMINAL_RESISTANCE = 10000.0  # 10k ohms at 25°C

# --- Hardware Precision Modifiers ---
SERIES_RESISTOR = 9810.0      # Your measured fixed resistor value
MAX_ADC_VALUE = 65535.0

# --- ADC Correction Factor ---
# Your board reads ~36070 when it mathematically should read ~29851.
# This scalar transparently cleans your Wemos S2 Mini's internal ADC drift.
ADC_SCALAR = 29851.0 / 36070.0 

while True:
    # 1. Capture the raw 16-bit value
    raw_adc = adc.read_u16()
    
    # 2. Apply hardware calibration scalar
    calibrated_adc = raw_adc * ADC_SCALAR
    
    # 3. Guard against boundary math errors
    if calibrated_adc >= MAX_ADC_VALUE:
        calibrated_adc = MAX_ADC_VALUE - 10
    elif calibrated_adc <= 0:
        calibrated_adc = 1

    # 4. Standard voltage divider formula (Thermistor to 3.3V, Reference to GND)
    resistance = SERIES_RESISTOR * ((MAX_ADC_VALUE / calibrated_adc) - 1.0)
    
    if resistance > 0:
        # 5. Clean, predictable Beta conversion equation
        temp_kelvin = 1.0 / ((1.0 / ROOM_TEMP_KELVIN) + (1.0 / BETA) * math.log(resistance / NOMINAL_RESISTANCE))
        
        temp_celsius = temp_kelvin - 273.15
        temp_fahrenheit = (temp_celsius * 9.0 / 5.0) + 32.0
        
        print("Raw 16-bit ADC: {:5d} | Resistance: {:.1f} Ω | Temp: {:.2f} °C".format(raw_adc, resistance, temp_celsius))
    else:
        print("Error: Invalid Resistance")
        
    time.sleep(1)
