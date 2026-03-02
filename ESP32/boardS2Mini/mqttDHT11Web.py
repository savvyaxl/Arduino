import alex.mqtt as MQTT
from alex.sensorDHT11 import SensorManager
from alex.webserver import WebServerHandler
import globals as g
import time
import ntptime
import select

try:
    ntptime.settime()
    print("Time synchronized!")
except:
    print("Failed to sync time")

print(f"Current time: {g.format_time(time.localtime(time.time() - 3 * 3600))}")

sensor_name="DHT11"
sensor_data=["Temperature", "Humidity"]
sensor = SensorManager(sensor_name, sensor_data)

mqtt = MQTT.MQTTHandler(sensor_name, sensor_data)
mqtt.connect()
mqtt.publish_config()

count_config_reset = time.ticks_ms()
count_print_time = time.ticks_ms()

ws = WebServerHandler()
server = ws.getServer()
poller = select.poll()
poller.register(server, select.POLLIN)

try:
    while True:
        if time.ticks_ms() - sensor.last_read_time > 60000:
            temp, hum = sensor.read()
            if mqtt and temp is not None and hum is not None:
                mqtt.publish(sensor.formatted_json())
        if time.ticks_ms() - count_config_reset > 3600000:
            count_config_reset = time.ticks_ms()
            if mqtt:
                mqtt.publish_config()
        if time.ticks_ms() - count_print_time > 10000:
            count_print_time = time.ticks_ms()
            #print(f"Current time: {time.localtime()}")
            print(f"Current time: {g.format_time(time.localtime(time.time() - 3 * 3600))}")

        try:
            if poller.poll(0):  # Check for incoming connections
                conn, addr = server.accept()
                print('Connection from', addr)
                request = conn.recv(1024).decode()
                print('Request:', request)
            
            
                # Extract the path from the request line
                request_line = request.splitlines()[0]
                path = request_line.split(" ")[1]

                HTTP_OK     = "HTTP/1.1 200 OK\r\n"
                ContentType = "Content-Type: text/html\r\n\r\n"

                if path == "/temp":
                    body = f"<h1>Temperature: {sensor.last_temperature}°C</h1>"
                elif path == "/humidity":
                    body = f"<h1>Humidity: {sensor.last_humidity}%</h1>"
                else:
                    body = f"<h1>Default: Temp {sensor.last_temperature}°C, Humidity {sensor.last_humidity}%</h1>"

                response = f"{HTTP_OK}{ContentType}<html><body>{body}</body></html>"

                conn.send(response.encode())
                conn.close()
        except Exception as e:
            print('Web server error:', e)
            

#        mqtt.check_msg()
        time.sleep(1)
except OSError as e:
    print(f"Error during MQTT operation: {e}")
finally:
    mqtt.disconnect()
    print("Disconnected from MQTT broker.")
