import asyncio

import machine # type: ignore
import time


class Stepper:

    # stepper={"step_pin": 4, "dir_pin": 2, "enable_pin": 39}
    def __init__(self, stepper=None):
        self.STEP_PIN = stepper["step_pin"]
        self.DIR_PIN = stepper["dir_pin"]
        self.ENABLE_PIN = stepper["enable_pin"]
        self.STEPS_PER_REV = 200 * 16
        self.ML_PER_REV = 1.2  
        self.STEPS_PER_ML = self.STEPS_PER_REV / self.ML_PER_REV
        self.enable = machine.Pin(self.ENABLE_PIN, machine.Pin.OUT)
        self.step = machine.Pin(self.STEP_PIN, machine.Pin.OUT)
        self.direction = machine.Pin(self.DIR_PIN, machine.Pin.OUT)

        # Most drivers are Active LOW (0 = Awake/On, 1 = Sleep/Off)
        self.enable.value(1) 


    async def pump_volume(self, pump={"ml": 5.5, "flow_rate_ml_min": 400.0, "clockwise": False}):
        # 1. Capture the start time
        start_time = time.ticks_ms()
        
        self.enable.value(0)
        await asyncio.sleep_ms(200)
        total_steps = int(pump["ml"] * self.STEPS_PER_ML)
        
        # Calculate the step delay required to match the target flow rate
        revs_per_min = pump["flow_rate_ml_min"] / self.ML_PER_REV
        steps_per_second = (revs_per_min / 60.0) * self.STEPS_PER_REV
        
        # Delay between step edges (half a cycle) in microseconds
        delay_us = int((1.0 / steps_per_second) * 1_000_000 / 2)
        
        self.direction.value(1 if pump["clockwise"] else 0)
        print(f"Dosing {pump['ml']}mL at {pump['flow_rate_ml_min']}mL/min...")
        print(f"Revs per minute...{revs_per_min}")
        
        for _ in range(total_steps):
            self.step.value(1)
            time.sleep_us(delay_us)
            self.step.value(0)
            time.sleep_us(delay_us)

        self.enable.value(1) 
        
        # 2. Calculate the difference and convert milliseconds to seconds
        duration_ms = time.ticks_diff(time.ticks_ms(), start_time)
        duration_sec = duration_ms / 1000.0
        
        print(f"Dosing complete. Took {duration_sec:.2f} seconds.")

    async def pump_volume_async(self, pump={"ml": 5.5, "flow_rate_ml_min": 400.0, "clockwise": False}):
        self.enable.value(0)
        await asyncio.sleep_ms(200)
        total_steps = int(pump["ml"] * self.STEPS_PER_ML)
        
        # Calculate the step delay required to match the target flow rate
        # Flow rate in revs per second = (flow_rate_ml_min / 60) / ML_PER_REV
        # Total steps per second = revs_per_second * STEPS_PER_REV
        revs_per_min = pump["flow_rate_ml_min"] / self.ML_PER_REV
        steps_per_second = (revs_per_min / 60.0) * self.STEPS_PER_REV
        
        # Delay between step edges (half a cycle) in microseconds
        delay_us = int((1.0 / steps_per_second) * 1_000_000 / 2)
        
        self.direction.value(1 if pump["clockwise"] else 0)
        print(f"Dosing {pump['ml']}mL at {pump['flow_rate_ml_min']}mL/min...")
        print(f"Revs per minute...{revs_per_min}")
        
        for _ in range(total_steps):
            self.step.value(1)
            time.sleep_us(delay_us)
            self.step.value(0)
            time.sleep_us(delay_us)

        self.enable.value(1) 
        print("Dosing complete.")


if __name__ == "__main__":
    pump = Stepper(stepper={"step_pin": 4, "dir_pin": 2, "enable_pin": 39})
    try:
        pump.pump_volume(pump={"ml": 5.5, "flow_rate_ml_min": 400.0, "clockwise": False})
    except KeyboardInterrupt:
        pass