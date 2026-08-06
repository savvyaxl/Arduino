import machine
import time
import network
from umqtt.simple import MQTTClient

# Configuration
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"
MQTT_BROKER = "YOUR_MQTT_BROKER_IP"
MQTT_CLIENT_ID = "ESP32_S2_Pump_Controller"
TOPIC_COMMAND = b"esp32/pump/command"
TOPIC_STATUS = b"esp32/pump/status"

# Hardware Setup (Using GPIO 5 as an example for the pump relay/MOSFET)
PUMP_PIN = 5
pump = machine.Pin(PUMP_PIN, machine.Pin.OUT)
pump.value(0) # Ensure pump starts OFF

# Global variables to store incoming message data
msg_received = False
pump_duration = 0

def mqtt_callback(topic, msg):
    global msg_received, pump_duration
    # Expecting message format payload like: b"START:30"
    message = msg.decode('utf-8')
    if message.startswith("START:"):
        try:
            pump_duration = int(message.split(":")[1])
            msg_received = True
        except ValueError:
            pass # Invalid number format received

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        # Wait up to 8 seconds for connection
        start_time = time.time()
        while not wlan.isconnected() and (time.time() - start_time) < 8:
            time.sleep_ms(100)
    return wlan.isconnected()

def main():
    global msg_received, pump_duration
    
    # 1. Attempt to connect to network
    if connect_wifi():
        try:
            # 2. Connect to MQTT Broker
            client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER)
            client.set_callback(mqtt_callback)
            client.connect()
            
            # Subscribe to the command queue
            client.subscribe(TOPIC_COMMAND)
            
            # 3. Check for messages briefly (poll the broker for 2 seconds)
            start_poll = time.ticks_ms()
            while (time.ticks_diff(time.ticks_ms(), start_poll) < 2000) and not msg_received:
                client.check_msg() # Checks if a queued/retained message arrived
                time.sleep_ms(50)
                
            # 4. If a valid start command was processed
            if msg_received and pump_duration > 0:
                # Log status and optionally clear the retained command
                client.publish(TOPIC_STATUS, b"running")
                client.publish(TOPIC_COMMAND, b"", retain=True) # Clears retained message
                
                # Turn pump ON
                pump.value(1)
                time.sleep(pump_duration) # Run for the programmed time
                pump.value(0) # Turn pump OFF
                
                client.publish(TOPIC_STATUS, b"done")
                time.sleep_ms(200) # Give network time to send packet
                
            client.disconnect()
        except Exception as e:
            print("MQTT or execution error:", e)
            
    # 5. Shut down Wi-Fi radio to save battery before deep sleep
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    
    # 6. Go to deep sleep for 5 minutes (300,000 milliseconds)
    print("Going to sleep...")
    machine.deepsleep(300000)

# Run the execution routine
main()
