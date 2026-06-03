# capacity_tester.py - A simple battery capacity tester for ESP32 using MicroPython

from machine import Pin, ADC, PWM
import time, json
from mqtt import MQTTHandler
import uasyncio as asyncio # type: ignore
import wifi_as as WiFi
import globals as g

class BatteryTester:

    def __init__(self, adc_pin_num=5, mosfet_pin_num=33, r_load=4.7, r1=46800, r2=9740, dutyMax = 1023):
        """
        :param adc_pin_num: GPIO for voltage divider
        :param mosfet_pin_num: GPIO for MOSFET gate
        :param r_load: Resistance of your load in Ohms
        :param r1: Resistance of the high-side resistor (connected to Battery +)
        :param r2: Resistance of the low-side resistor (connected to GND)
        """
        # self.load_pin = Pin(mosfet_pin_num, Pin.OUT)
        self.load_pin = PWM(Pin(mosfet_pin_num), freq=5000)
        self.adc = ADC(Pin(adc_pin_num))
        self.adc.atten(ADC.ATTN_11DB)
        self.dutyMax = dutyMax
        self.mqtt = MQTTHandler()
        
        self.r_load = r_load
        # Automated ratio calculation: (R1 + R2) / R2
        self.v_ratio = (r1 + r2) / ( r2 / 0.9832 )
        
        self.capacity_ah = 0.0
        self.is_running = False
        
        self.initial_voltage = 0
        self.initial_ir = 0
        self.IR = 0
        
        self.mac = None
        self.type = None
        self.base_topic = None
        
        print(f"Tester Initialized. Calculated Divider Ratio: {self.v_ratio:.3f}")

    def announce_to_home_assistant(self):

            
            
        names = {
            "Bettery Tester Amp hours": {
                "type": "sensor",
                "unit": "Ah"
            },
            "Bettery Tester Volts": {
                "type": "sensor",
                "unit": "V"
            },
            "Bettery Tester Watts": {
                "type": "sensor",
                "unit": "W"
            },
            "Bettery Tester Amps": {
                "type": "sensor",
                "unit": "A"
            },
            "Bettery Tester Count": {
                "type": "sensor"
            },
            "Bettery Tester IR": {
                "type": "sensor",
                "unit": "mΩ"
            }
        }
        
        for name, info in names.items():
            clean_name = name.lower().replace(" ", "_")
            if g.mac:
                type = info["type"]
                self.base_topic = f"homeassistant/{type}/{g.mac}"

            # 1. Start with the mandatory fields
            config_payload = {
                "name": name,
                "unique_id": f"esp32_{clean_name}",
                "state_topic": f"{self.base_topic}/state",
                "value_template": "{{ value_json." + clean_name + " }}",
                "device": {
                    "identifiers": [f"esp32_{g.mac}"],
                    "name": "Battery Tester ESP32"
                }
            }

            # 2. Only add optional items if they have a value
            if info.get("unit"):
                config_payload["unit_of_measurement"] = info["unit"]

            if info.get("device_class"):
                config_payload["device_class"] = info["device_class"]
                
            config_topic = f"{self.base_topic}/{clean_name}/config"
            try:
                self.mqtt.publish_config(config_topic, json.dumps(config_payload))
                print(f"Published Home Assistant config for {name} to {config_topic}")
            except Exception as e:
                print(f"Error occurred while publishing MQTT config for {name}: {e}")



    def get_voltage(self, samples = 150):
        """Reads calibrated microvolts and returns actual battery voltage."""
        raw_uv = 0        
        for _ in range(samples):
            raw_uv += self.adc.read_uv()
        v_pin = (raw_uv / samples) / 1000000
        return v_pin * self.v_ratio

    def run_test(self, cutoff_v=10.5, interval=1):
        """Starts the discharge test. Blocks until complete."""
        self.initial_voltage = self.get_voltage()
        print(f"Starting test: Load={self.r_load}Ω, Cutoff={cutoff_v}V, Initial Voltage={round(self.initial_voltage, 2)}")
        self.capacity_ah = 0.0
        self.load_pin.duty(self.dutyMax) 
        self.is_running = True
        _count = 0
        try:
            while self.is_running:
                v_bat = self.get_voltage()
                current = v_bat / self.r_load
                watts = current * v_bat
                self.capacity_ah += current * (interval / 3600)
                
                if _count == 0 :
                    self.IR = ( ( self.initial_voltage - v_bat ) / current ) * 1000
                    print(f"V: {v_bat:.2f}V | I: {current:.2f}A | W: {watts:.2f}W | Ah: {self.capacity_ah:.4f} | Seconds: {_count} | IR: {round(self.IR, 0)}" )
                else:
                    print(f"V: {v_bat:.2f}V | I: {current:.2f}A | W: {watts:.2f}W | Ah: {self.capacity_ah:.4f} | Seconds: {_count}")
                
                if v_bat <= cutoff_v:
                    self.stop_test("Cutoff Reached")
                    break
                
                _count += interval
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stop_test("User Interrupted")

    

    def run_test_mqtt(self, cutoff_v=10.5, interval=1):
        _count = 0
        """Starts discharge and yields a JSON string for MQTT publishing."""
        self.initial_voltage = self.get_voltage()
        print(f"Starting test: Load={self.r_load}Ω, Cutoff={cutoff_v}V, Initial Voltage={round(self.initial_voltage, 2)}")
        self.capacity_ah = 0.0
        self.load_pin.duty(self.dutyMax)
        self.is_running = True

        try:
            while self.is_running:
                v_bat = self.get_voltage()
                current = v_bat / self.r_load
                watts = current * v_bat
                self.capacity_ah += current * (interval / 3600)
                if _count == 0 :
                    self.IR = ( ( self.initial_voltage - v_bat ) / current ) * 1000
                    print(f"V: {v_bat:.2f}V | I: {current:.2f}A | W: {watts:.2f}W | Ah: {self.capacity_ah:.4f} | Seconds: {_count} | IR: {round(self.IR, 0)}" )
                else:
                    print(f"V: {v_bat:.2f}V | I: {current:.2f}A | W: {watts:.2f}W | Ah: {self.capacity_ah:.4f} | Seconds: {_count}")
                
                # Create the data payload
                data = {
                    "bettery_tester_volts": round(v_bat, 3),
                    "bettery_tester_amps": round(current, 3),
                    "bettery_tester_amp_hours": round(self.capacity_ah, 5),
                    "bettery_tester_watts": round(watts, 5),
                    "bettery_tester_ir": round(self.IR, 0),
                    "bettery_tester_count": _count,
                    "status": "discharging"
                }
                
                #print(f"publishing {data}")
                # Yield the JSON string back to the caller
                yield json.dumps(data)
                #mqtt.publish("sam", json.dumps(data))

                if v_bat <= cutoff_v:
                    self.stop_test("Cutoff Reached")
                    break
                _count += interval    
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stop_test("User Interrupted")

    def stop_test(self, reason="Stopped"):
        self.load_pin.duty(0)  # Set PWM duty cycle to 0%
        self.is_running = False
        print(f"Test {reason}. Final Capacity: {self.capacity_ah:.4f} Ah with an internal resistance of {round(self.IR, 0)} mOhm")

    def read_voltage(self, maxcount=3, interval=1):
        """Starts the discharge test. Blocks until complete."""

        self.load_pin.duty(0) 
        self.is_running = True
        count = 0
        try:
            while self.is_running and count < maxcount:
                v_bat = self.get_voltage()
                print(f"Count: {count} | V: {v_bat:.2f}V")
                
                if maxcount <= count:
                    self.stop_test("Time Reached")
                    break
                
                count += 1
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stop_test("User Interrupted")
            
    def run(self):


        try:
            self.mqtt.connect()
        except Exception as e:
            print(f"Error in run occurred while connecting to MQTT: {e}")

        try:
            self.announce_to_home_assistant()
        except Exception as e:
            print(f"Error in run publish config in MQTT: {e}")

        try:
            #self.run_test_mqtt(cutoff_v=3.0, interval=1)
            
            for mqtt_json in self.run_test_mqtt(cutoff_v=3.0, interval=1):
                # 'client' would be your Umqtt.simple instance
                try:
                    self.mqtt.publish(f"{self.base_topic}/state", mqtt_json)
                except Exception as e:
                    print(f"Failed to publish MQTT message: {e}")

            
        except Exception as e:
            print(f"Error in run publish status in MQTT: {e}")

# --- 3. Entry Point ---
if __name__ == "__main__":
    tester = BatteryTester(adc_pin_num=5, mosfet_pin_num=33, r_load=4.7, r1=46800, r2=9740, dutyMax = 1023)
    try:
        tester.read_voltage(maxcount=3)
        tester.run_test(cutoff_v=3, interval=1)
    except KeyboardInterrupt:
        pass
