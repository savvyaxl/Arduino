import alex.board as board
import machine

# Blink onboard LED
board.LED.on()

# Read from IO4 (ADC-capable)
adc = machine.ADC(board.IO4)
print(adc.read_u16())

# I2C scan
i2c = board.I2C()
print(i2c.scan())

# UART write
uart = board.UART()
uart.write("Hello LOLIN S2 Mini\n")
print("Print: Hello LOLIN S2 Mini\n")


import time

# Blink onboard LED
led = board.LED
while True:
    led.on()
    time.sleep(0.5)
    led.off()
    time.sleep(0.5)
