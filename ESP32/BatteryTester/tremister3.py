from machine import Pin, ADC
import math
import time

# --- Configuration ---
adc_pin = Pin(7, Pin.IN)
adc = ADC(adc_pin)
adc.atten(ADC.ATTN_11DB)  # Configures pin range for standard 3.3V reference

# Steinhart-Hart Coefficients for a standard 10k NTC thermistor
#A = 0.001129148
#B = 0.000234125
#C = 0.0000000876741

A = 0.1089202450e-3
B = 3.835926653e-4
C = -3.372025351e-7

SERIES_RESISTOR = 9810.0  # 10k ohm fixed reference resistor
MAX_ADC_VALUE = 65535    # 16-bit Full Scale ceiling for read_u16()


def get_voltage(samples = 150):
    """Reads calibrated microvolts and returns actual battery voltage."""
    raw_uv = 0        
    for _ in range(samples):
        raw_uv += adc.read_u16()
    return (raw_uv / samples)


while True:
    # Read using 16-bit resolution (Universal MicroPython standard)
    
    adc_val = get_voltage()
    
    # Boundary padding to secure calculations from division errors
    if adc_val >= MAX_ADC_VALUE:
        adc_val = MAX_ADC_VALUE - 10
    elif adc_val <= 0:
        adc_val = 1

    # Voltage divider formula: Assumes Thermistor to 3.3V, Fixed Resistor to GND
    resistance = SERIES_RESISTOR * ((MAX_ADC_VALUE / adc_val) - 1.0)
    #resistance = SERIES_RESISTOR / ((MAX_ADC_VALUE / adc_val) - 1.0)
    
    if resistance > 0:
        log_r = math.log(resistance)
        temp_kelvin = 1.0 / (A + (B * log_r) + (C * log_r**3))
        
        temp_celsius = temp_kelvin - 273.15 - 10.5
        
        print("Raw 16-bit ADC: {:5d} | Resistance: {:.1f} Ω | Temp: {:.2f} °C".format(int(adc_val), resistance, temp_celsius))
    else:
        print("Raw ADC: {} | Error: Invalid Resistance".format(adc_val))
        
    time.sleep(1)
