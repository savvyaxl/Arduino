
from machine import Pin, SoftI2C # type: ignore
import ssd1306
import onewire # type: ignore
import ds18x20 # type: ignore
from time import sleep
from writer import Writer
import freesans20
import courier20
import sys

# Use SoftI2C to avoid peripheral conflicts
i2c = SoftI2C(scl=Pin(7), sda=Pin(9))

# Test scanning for the display address (should print [60] or [0x3C])
print("I2C Scan:", i2c.scan())
ow = onewire.OneWire(Pin(5))  # Initialize OneWire on GPIO 5
ds_sensor = ds18x20.DS18X20(ow)

# Define display size
width = 128
height = 64

# Create the display object (default I2C address is 0x3C)
oled = ssd1306.SSD1306_I2C(width, height, i2c)
w = Writer(oled, courier20)

# Updated database mapping your sensor ROM to the corrected slope and intercept
CALIBRATION_MAP = {
    "2894816b00000071": (0.98172, -0.16892), 
}
#    "2894816b00000071": (1.00380, -1.89291), 
def ds18x20_loop():
    #print("MQTT DS18X20 Sender Task started...")
    while True:
        try:
            #print("Scanning for 1-Wire devices...")
            roms = ds_sensor.scan()
            #print(f"Found {len(roms)} Dallas temperature sensor(s).")

            if not roms:
                print("No sensors found. Check your wiring and pull-up resistor.")
                return
            
        except Exception as e:
            print(f"Error occurred while reading DS18X20 sensor: {e}")
        #sleep(10)  # Send every 10 seconds

        try:
            # Start temperature conversion across all sensors
            ds_sensor.convert_temp()
            
            # Yield control to the event loop during the 750ms conversion time
            sleep(1)
            
            # Read data from each discovered sensor
            for rom in roms:
                rom_address = ''.join(['{:02x}'.format(b) for b in rom])
                temp_c = ds_sensor.read_temp(rom)
                
                # Check if the address doesn't exist in your mapping dictionary
                if rom_address not in CALIBRATION_MAP:
                    print(f"ALERT: Unregistered sensor found! ROM: {rom_address}")
                
                # Grab calibration tuple or default to safe uncalibrated bypass (1.0, 0.0)
                multiplier, offset = CALIBRATION_MAP.get(rom_address, (1.0, 0.0))
                
                # Calculate real temperature: (reading * m) + c
                calibrated_temp = (temp_c * multiplier) + offset
                
                print(f"Temp: {temp_c:.2f}°C")
                Writer.set_textpos(oled, 0, 0)
                #w.printstring(f"Temp: {temp_c:.2f} {calibrated_temp:.2f} C")
                w.printstring(f"012345678 {temp_c:.2f} 012345678")
                oled.show()
          

        except Exception as e:
            print(f"Error occurred while reading DS18X20 sensor: {e}")




ds18x20_loop()