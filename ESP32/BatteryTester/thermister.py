from machine import Pin, ADC
import math
import time

# --- Configuration ---
adc_pin = Pin(7, Pin.IN)
adc = ADC(adc_pin)
adc.atten(ADC.ATTN_11DB)

# --- Calibrated Steinhart-Hart Coefficients ---
# Calculated for: 11000 Ohms @ 20°C & 10000 Ohms @ 25°C
A = 0.1089202450e-3
B = 3.835926653e-4
C = -3.372025351e-7

SERIES_RESISTOR = 9810.0   # Your physically measured fixed resistor value
MAX_ADC_VALUE = 65535.0    # 16-bit Full Scale ceiling for read_u16()

while True:
    # Read using 16-bit resolution (Universal MicroPython standard)
    adc_val = adc.read_u16()
    
    # Boundary padding to secure calculations from division errors
    if adc_val >= MAX_ADC_VALUE:
        adc_val = MAX_ADC_VALUE - 10
    elif adc_val <= 0:
        adc_val = 1

    # Voltage divider formula: Assumes Thermistor to 3.3V, Fixed Resistor to GND
    resistance = SERIES_RESISTOR * ((MAX_ADC_VALUE / adc_val) - 1.0)
    if resistance > 0:
        # Steinhart-Hart Conversion
        log_r = math.log(resistance)
        temp_kelvin = 1.0 / (A + (B * log_r) + (C * log_r**3))
        
        temp_celsius = temp_kelvin - 273.15
        temp_fahrenheit = (temp_celsius * 9.0 / 5.0) + 32.0
        
        print("Raw 16-bit ADC: {:5d} | Resistance: {:.1f} Ω | Temp: {:.2f} °C | Temp: {:.2f} °K".format(adc_val, resistance, temp_celsius, temp_kelvin))
    else:
        print("Raw ADC: {} | Error: Invalid Resistance".format(adc_val))
        
    time.sleep(1)
