import asyncio
from machine import Pin
import onewire
import ds18x20

# 1. Initialize the GPIO pin and the OneWire bus
data_pin = Pin(4)
ow = onewire.OneWire(data_pin)

# 2. Create the DS18X20 sensor driver object
ds_sensor = ds18x20.DS18X20(ow)

async def read_temperature():
    # 3. Scan the bus to find all connected Dallas sensors
    print("Scanning for 1-Wire devices...")
    roms = ds_sensor.scan()
    print(f"Found {len(roms)} Dallas temperature sensor(s).")
    
    if not roms:
        print("No sensors found. Check your wiring and pull-up resistor.")
        return

    # 4. Continuous asynchronous reading loop
    while True:
        try:
            # Start temperature conversion across all sensors
            ds_sensor.convert_temp()
            
            # Yield control to the event loop during the 750ms conversion time
            await asyncio.sleep_ms(750)
            
            # Read data from each discovered sensor
            for rom in roms:
                rom_address = ''.join(['{:02x}'.format(b) for b in rom])
                temp_c = ds_sensor.read_temp(rom)
                temp_f = (temp_c * 9/5) + 32
                
                print(f"Sensor [{rom_address}] -> Temp: {temp_c:.2f}°C | {temp_f:.2f}°F")
                
        except Exception as e:
            print("Error reading sensor:", e)
            
        print("-" * 40)
        # Yield control for 2 seconds before the next reading loop
        await asyncio.sleep(2)

async def other_background_task():
    # Example task running concurrently alongside the temperature readings
    while True:
        print("[Task] Running background process concurrently...")
        await asyncio.sleep(1)

async def main():
    # Start both tasks concurrently
    await asyncio.gather(
        read_temperature(),
        other_background_task()
    )

# Start the event loop
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Program stopped by user.")
