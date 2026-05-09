# capacity_tester.py - A simple battery capacity tester for ESP32 using MicroPython

from machine import Pin, ADC
import time
import json

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

    def get_voltage(self):
        """Reads calibrated microvolts and returns actual battery voltage."""
        raw_uv = 0
        for _ in range(20):
            raw_uv += self.adc.read_uv()
        v_pin = (raw_uv / 20) / 1000000
        return v_pin * self.v_ratio

    def run_test(self, cutoff_v=10.5, interval=1):
        """Starts the discharge test. Blocks until complete."""
        print(f"Starting test: Load={self.r_load}Ω, Cutoff={cutoff_v}V")
        self.capacity_ah = 0.0
        self.load_pin.value(1) 
        self.is_running = True
        
        try:
            while self.is_running:
                v_bat = self.get_voltage()
                current = v_bat / self.r_load
                self.capacity_ah += current * (interval / 3600)
                
                print(f"V: {v_bat:.2f}V | I: {current:.2f}A | Ah: {self.capacity_ah:.4f}")
                
                if v_bat <= cutoff_v:
                    self.stop_test("Cutoff Reached")
                    break 
                
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stop_test("User Interrupted")

    

    def run_test_mqtt(self, cutoff_v=10.5, interval=1):
        """Starts discharge and yields a JSON string for MQTT publishing."""
        print(f"Starting test: Load={self.r_load}Ω, Cutoff={cutoff_v}V")
        self.capacity_ah = 0.0
        self.load_pin.value(1)
        self.is_running = True

        try:
            while self.is_running:
                v_bat = self.get_voltage()
                current = v_bat / self.r_load
                self.capacity_ah += current * (interval / 3600)
                
                # Create the data payload
                data = {
                    "VoltageBattery": round(v_bat, 3),
                    "CurrentBattery": round(current, 3),
                    "EnergyBattery": round(self.capacity_ah, 5),
                    "status": "discharging"
                }
                
                # Yield the JSON string back to the caller
                yield json.dumps(data)

                if v_bat <= cutoff_v:
                    self.stop_test("Cutoff Reached")
                    break
                    
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stop_test("User Interrupted")

    def stop_test(self, reason="Stopped"):
        self.load_pin.value(0)
        self.is_running = False
        print(f"Test {reason}. Final Capacity: {self.capacity_ah:.4f} Ah")

    def read_voltage(self, maxcount=30, interval=1):
        """Starts the discharge test. Blocks until complete."""

        self.load_pin.value(0) 
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
            

# import json
# # inside your loop:
# data = {
#     "voltage": v_bat,
#     "current": current,
#     "capacity_ah": self.capacity_ah,
#     "status": "discharging"
# }
# mqtt.publish("battery/tester/state", json.dumps(data))