import machine
import time

# Configure GPIO 34 as an Analog Pin
rain_pin = machine.ADC(machine.Pin(34))

# Set 11dB attenuation to read the full 0V to 3.3V range
rain_pin.atten(machine.ADC.ATTN_11DB)

print("Starting Rain Sensor Monitoring...")

while True:
    # Read analog value (returns a number between 0 and 4095)
    rain_value = rain_pin.read()
    
    print("Raw Sensor Value:", rain_value)
    
    # Analyze the moisture levels based on the 12-bit range
    if rain_value < 1500:
        print("Status: Heavy Rain! 🌧️")
    elif rain_value < 3000:
        print("Status: Light Rain / Drizzle 🌦️")
    else:
        print("Status: Dry ☀️")
        
    print("-" * 30)
    time.sleep(1)  # Wait 1 second before reading again
