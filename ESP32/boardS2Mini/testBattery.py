import alex.mqtt as MQTT
import time
import ntptime
import globals as g
from alex.capacity_tester import BatteryTester # Assuming your class is in this file

try:
    ntptime.settime()
    print("Time synchronized!")
    print(f"{g.format_time(time.localtime(time.time() - 3 * 3600))}")
except:
    print("Failed to sync time")

sensor_name="Battery"
sensor_data=["Current", "Voltage", "Energy"]
#sensor = SensorManager(sensor_name, sensor_data)

mqtt = MQTT.MQTTHandler(sensor_name, sensor_data)
mqtt.connect()
mqtt.publish_config()

tester = BatteryTester(adc_pin_num=4, mosfet_pin_num=33, r_load=35.3)

# Use a loop to catch every JSON update yielded by the generator
for mqtt_json in tester.run_test_mqtt(cutoff_v=10.5, interval=10):
    # 'client' would be your Umqtt.simple instance
    mqtt.publish(mqtt_json)

# 1. SETUP
# Use the pins from the diagram: ADC=34, MOSFET=32
# Use your measured resistance: 35.3 ohms
#tester = BatteryTester(adc_pin_num=4, mosfet_pin_num=33, r_load=35.3)
#tester.read_voltage(maxcount=30, interval=1)
#tester.run_test(cutoff_v=10.5, interval=1)
