import dht
import machine
import time
import json
import globals as g

class SensorManager:
    def __init__(self, sensor_name="ESP32a", sensor_data=["Temperature", "Humidity"], pin=18 ):
        self.dht = dht.DHT11(machine.Pin(pin))
        self.last_temperature = None
        self.last_humidity = None
        self.last_read_time = 0
        self.sensor_name = sensor_name
        self.sensor_data = sensor_data
        self.sensor_units = {
            "temperature": "°C",
            "humidity": "%",
            "pressure": "hPa",
            "co2": "ppm",
            # Add more sensor types and units as needed
        }



    def read(self):
        try:
            self.dht.measure()
            self.last_temperature = self.dht.temperature()
            self.last_humidity = self.dht.humidity()
            self.last_read_time = time.ticks_ms()
            return self.last_temperature, self.last_humidity
        except OSError as e:
            print(f"Sensor read error: {e}")
            self.last_temperature = None
            self.last_humidity = None
            return None, None

    def formatted_json(self):
        data = {}
        for sensor in self.sensor_data:
            attr_name = f"last_{sensor.lower()}"
            value = getattr(self, attr_name, None)
            if value is not None:
                key = f"{sensor}{self.sensor_name}"
                data[key] = value
        return json.dumps(data) if data else "{}"

    def formatted_sensor_config(self, sensor):
        data = {}
        sen = f"{sensor}{sensor_name}"
        unit = self.sensor_units.get(sensor.lower(), "")
        data["device_class"] = f"{sensor.lower()}"
        data["name"] = sen
        data["unit_of_measurement"] = unit
        data["value_template"] = "{{{{value_json.{sen}}}}}"
        data["state_topic"] = f"homeassistant/sensor/{g.mac}/{sen}/state"
        return json.dumps(data) if data else "{}"


