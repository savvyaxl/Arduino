from machine import Pin # type: ignore
from time import sleep
import dht

# Initialize the DHT11 sensor on GPIO 4
sensor = dht.DHT11(Pin(5))

while True:
    try:
        # Wait at least 1 second between readings
        sleep(2)
        
        # Trigger the sensor to measure the environment
        sensor.measure()
        
        # Extract the values
        temp = sensor.temperature()
        hum = sensor.humidity()
        
        # Print the values to the shell
        print("Temperature: {}°C".format(temp))
        print("Humidity: {}%".format(hum))
        
    except OSError as e:
        print("Failed to read sensor!")
