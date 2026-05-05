import alex.mqtt as MQTT
import time
import ntptime # type: ignore
import globals as g
from alex.capacity_tester import BatteryTester # Assuming your class is in this file
import alex.wifi as WiFi
from alex.alarm import TimeSync, AlarmDaily, AlarmWeekly # For time synchronization and alarm management

sensor_name="Battery"
sensor_data=["Current", "Voltage", "Energy"]
#sensor = SensorManager(sensor_name, sensor_data)

mqtt = MQTT.MQTTHandler(sensor_name, sensor_data)
mqtt.connect()
mqtt.publish_config()

tester = BatteryTester(adc_pin_num=4, mosfet_pin_num=33, r_load=35.3)

syncTimeHours = 4
checkSeconds = 30
sync = TimeSync() # Initialize time synchronization (optional, but recommended for accurate alarms)
daily = AlarmDaily()
daily.add_alarm(20, 53, 0, lambda: print("1 BEEP BEEP!")) 
daily.add_alarm(20, 53, 20, lambda: print("2 BEEP BEEP!")) 
daily.list_alarms()
weekly = AlarmWeekly()
weekly.add_weekly_alarm([0, 2, 4], 8, 0, 0, lambda: print("Time to work!")) 
weekly.list_alarms()

ticker = time.time()

while True:
    # print(sync.getTime()) # Optional: Print current time for debugging
    if time.time() - sync.last_ntp_sync >= 3600 * syncTimeHours: sync.sync_ntp()
    weekly.check_alarms()
    daily.check_alarms()
    time.sleep(0.5)

# # Use a loop to catch every JSON update yielded by the generator
# for mqtt_json in tester.run_test_mqtt(cutoff_v=10.5, interval=10):
#     # 'client' would be your Umqtt.simple instance
#     try:
#         mqtt.publish(mqtt_json)
#     except Exception as e:
#         print(f"Failed to publish MQTT message: {e}")
#         if not WiFi.wlan.isconnected():
#             WiFi.reconnect_wifi()
#             try:
#                 mqtt.check_msg()
#             except Exception as e:
#                 mqtt.connect()  # Reconnect MQTT if needed
#                 mqtt.publish_config()

# 1. SETUP
# Use the pins from the diagram: ADC=34, MOSFET=32
# Use your measured resistance: 35.3 ohms
#tester = BatteryTester(adc_pin_num=4, mosfet_pin_num=33, r_load=35.3)
#tester.read_voltage(maxcount=30, interval=1)
#tester.run_test(cutoff_v=10.5, interval=1)
