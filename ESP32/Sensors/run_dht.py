import uasyncio as asyncio # type: ignore
from machine import Pin # type: ignore
import dht

# Initialize the DHT11 sensor on GPIO 5
sensor = dht.DHT11(Pin(5))

async def read_sensor():
    while True:
        try:
            # Non-blocking sleep allows other tasks to run
            await asyncio.sleep(2) 
            
            sensor.measure()
            temp = sensor.temperature()
            hum = sensor.humidity()
            
            print("Temperature: {}°C".format(temp))
            print("Humidity: {}%".format(hum))
            
        except OSError as e:
            print("Failed to read sensor!")

async def main():
    # Start the sensor task
    asyncio.create_task(read_sensor())
    
    # Keep the main loop alive or run other tasks here
    while True:
        await asyncio.sleep(1)

# Start the async loop
asyncio.run(main())
