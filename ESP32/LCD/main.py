import time
from machine import Pin
from gpio_lcd import GpioLcd

# Define the hardware connections based on your wiring
# Syntax: GpioLcd(rs_pin, enable_pin, d4_pin, d5_pin, d6_pin, d7_pin, num_lines, num_columns)
lcd = GpioLcd(
    rs_pin=Pin(2),
    enable_pin=Pin(3),
    d4_pin=Pin(4),
    d5_pin=Pin(5),
    d6_pin=Pin(7),
    d7_pin=Pin(9),
    num_lines=2,
    num_columns=16
)

# Clear the screen
lcd.clear()

# Print text to the display
lcd.putstr("Hello, World!\n")
lcd.putstr("ESP32-S2 Mini")

while True:
    # Keep the program running
    time.sleep(1)
