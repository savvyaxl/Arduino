
import uasyncio as asyncio # type: ignore
from SmartHomeManager import SmartHomeManager

# owPin is the pin for the 1-wire bus (DS18B20 temperature sensors), owPin=3
# ssd1306 is the oled display, ssd1306={"scl": 7, "sda": 9}
# stepper_config defines the pins for the stepper motor, stepper_config={"step_pin": 4, "dir_pin": 2, "enable_pin": 39}
manager = SmartHomeManager(stepper_config={"step_pin": 4, "dir_pin": 2, "enable_pin": 39})
try:
    asyncio.run(manager.run())
except KeyboardInterrupt:
    pass
