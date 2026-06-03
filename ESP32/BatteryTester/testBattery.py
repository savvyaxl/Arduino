import mqtt as MQTT
import time, json
import ntptime # type: ignore
import globals as g
from capacity_tester import BatteryTester # Assuming your class is in this file
import wifi_as as WiFi
from machine import Pin, ADC

class BatteryTester:
    def __init__(self, adc_pin_num, mosfet_pin_num, r_load=10.0, r1=9770, r2=2153):
        """
        :param adc_pin_num: GPIO for voltage divider
        :param mosfet_pin_num: GPIO for MOSFET gate
        :param r_load: Resistance of your load in Ohms
        :param r1: Resistance of the high-side resistor (connected to Battery +)
        :param r2: Resistance of the low-side resistor (connected to GND)
        """
        self.load_pin = Pin(mosfet_pin_num, Pin.OUT)
        self.adc = ADC(Pin(adc_pin_num))
        self.adc.atten(ADC.ATTN_11DB) 
        
        self.r_load = r_load
        # Automated ratio calculation: (R1 + R2) / R2
        self.v_ratio = (r1 + r2) / ( r2 / 0.9832 )
        
        self.capacity_ah = 0.0
        self.is_running = False
        
        print(f"Tester Initialized. Calculated Divider Ratio: {self.v_ratio:.3f}")

    # try:
    #     ntptime.settime()
    #     print("Time synchronized!")
    #     print(f"{g.format_time(time.localtime(time.time() - 3 * 3600))}")
    # except:
    #     print("Failed to sync time")

    sensor_name="Battery"
    sensor_data=["Current", "Voltage", "Energy"]
    #sensor = SensorManager(sensor_name, sensor_data)

    mqtt = MQTT.MQTTHandler(sensor_name, sensor_data)
    mqtt.connect()
    mqtt.publish_config("bob","sam")

    #tester = BatteryTester(adc_pin_num=5, mosfet_pin_num=33, r_load=2.8, r1=46800, r2=9740)


    #tester.read_voltage(maxcount=30, interval=1)

    # Use a loop to catch every JSON update yielded by the generator
    for mqtt_json in tester.run_test_mqtt(cutoff_v=10.5, interval=11):
        # 'client' would be your Umqtt.simple instance
        try:
            mqtt.publish("bob",mqtt_json)
        except Exception as e:
            print(f"Failed to publish MQTT message: {e}")
            if not WiFi.wlan.isconnected():
                WiFi.reconnect_wifi()
                try:
                    mqtt.check_msg()
                except Exception as e:
                    mqtt.connect()  # Reconnect MQTT if needed
                    mqtt.publish_config()

    # 1. SETUP
    # Use the pins from the diagram: ADC=34, MOSFET=32
    # Use your measured resistance: 35.3 ohms
    #tester = BatteryTester(adc_pin_num=4, mosfet_pin_num=33, r_load=35.3)
    #tester.read_voltage(maxcount=30, interval=1)
    #tester.run_test(cutoff_v=3.0, interval=1)
