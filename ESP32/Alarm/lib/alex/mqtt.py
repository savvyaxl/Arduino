import sys
import time
from umqtt.simple import MQTTClient
import globals as g
import json
import ssl
from collections import deque # Or use a simple list

# Create SSL context
context = None
if g.mqport == 8883:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.verify_mode = ssl.CERT_NONE
    if g.broker == f"mqtt.savvyaxl.com.br":
        context.verify_mode = ssl.CERT_REQUIRED
    context.load_cert_chain(certfile="client.crt", keyfile="client.key")
    context.load_verify_locations(cafile="CA.crt")

class MQTTHandler:
    def __init__(
        self,
        sensor_name="DHT11",
        sensor_data=["Temperature", "Humidity"],
        client_id=f"micropython_test_client_{g.mac}"
    ):
        self.sensor_name = sensor_name
        self.sensor_data = sensor_data
        self.client_id = client_id
        self.state_topic = f"homeassistant/sensor/{g.mac}/state"
        self.sub_topic = f"homeassistant/sensor/{g.mac}/subscribe"
        self.client = MQTTClient(
            client_id,
            g.broker,
            g.mqport,
            g.mquser,
            g.mqpass,
            ssl=context
            )
        self.client.set_callback(self.sub_cb)
        self.sensor_units = {
            "temperature": "°C",
            "humidity": "%",
            "pressure": "hPa",
            "co2": "ppm",
            "current": "A",
            "voltage": "V",
            "energy": "Wh",
            
            # Add more sensor types and units as needed
        }
        self.queue = deque((), 10)

    def sub_cb(self, topic, msg):
        print(f"Received message from topic '{topic.decode()}': {msg.decode()}")
        print(f"DEBUG: Adding to queue. Current size: {len(self.queue)}")
        self.queue.append((topic.decode(), msg.decode()))

    def connect(self):
        print(f"Connecting to MQTT broker {g.broker}:{g.mqport}...")
        try:
            self.client.connect()
            print(f"Connected to MQTT broker at {g.broker}")
            # self.client.subscribe(self.sub_topic)
            # print(f"Subscribed to topic: {self.sub_topic}")
        except OSError as e:
            print(f"Failed to connect or subscribe: {e}")

    def subscribe(self, topic):
        try:
            self.client.subscribe(topic)
            print(f"Subscribed to topic: {topic}")
        except OSError as e:
            print(f"Failed to subscribe to topic '{topic}': {e}")

    def disconnect(self):
        print(f"Disconnecting from MQTT broker {g.broker}:{g.mqport}...")
        try:
            self.client.disconnect()
        except OSError as e:
            print(f"Failed to disconnect: {e}")

    def check_msg(self):
        try:
            self.client.check_msg()
        except OSError as e:
            print(f"Error during check_msg operation: {e}")
            raise Exception(f"{e}")

    def on_message_received(self, topic, msg):
        # Convert bytes to string
        t = topic.decode()
        m = msg.decode()
        
        print(f"Received {m} on {t}")
        return m
    
    def publish(self, topic=None, message=None):
        try:
            if message is None:
                message = f'Hello from MicroPython at {time.time()}'
            if topic is None:
                topic = self.state_topic
            self.client.publish(topic, message.encode())
            print(f"Published message to '{topic}': {message}")
        except OSError as e:
            print(f"Error during publish operation: {e}")
            raise Exception(f"{e}")

    def publish_config(self, topic, msg):
            try:
                self.client.publish(topic, msg.encode(), retain=True)
                #print(f"Published config to '{topic}': {msg}")
            except OSError as e:
                func_name = sys._getframe().f_code.co_name 
                print(f"Error in {func_name} Publishing config to '{topic}': {msg}: {e}")
                raise Exception(f"{e}")

    def formatted_config(self, sensor):
        data = {}
        sen = f"{sensor}{self.sensor_name}"
        unit = self.sensor_units.get(sensor.lower(), "")
        data["device_class"] = f"{sensor.lower()}"
        data["name"] = sen
        data["unit_of_measurement"] = unit
        data["value_template"] = f"{{{{value_json.{sen}}}}}"
        data["state_topic"] = self.state_topic
        return json.dumps(data) if data else "{}"
