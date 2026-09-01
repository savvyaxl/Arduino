import machine # type: ignore
import time


class stepper:

    def __init__(self, stepper={"step_pin": 4, "dir_pin": 2, "enable_pin": 39}):
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


    def pump_volume(self, ml, flow_rate_ml_min, clockwise=False):
        """
        Doses a precise volume of liquid at a designated flow rate.
        :param ml: Total volume to dispense in milliliters
        :param flow_rate_ml_min: Flow rate target in mL per minute
        """
        total_steps = int(ml * self.STEPS_PER_ML)
        
        # Calculate the step delay required to match the target flow rate
        # Flow rate in revs per second = (flow_rate_ml_min / 60) / ML_PER_REV
        # Total steps per second = revs_per_second * STEPS_PER_REV
        revs_per_min = flow_rate_ml_min / self.ML_PER_REV
        steps_per_second = (revs_per_min / 60.0) * self.STEPS_PER_REV
        
        # Delay between step edges (half a cycle) in microseconds
        delay_us = int((1.0 / steps_per_second) * 1_000_000 / 2)
        
        self.direction.value(1 if clockwise else 0)
        print(f"Dosing {ml}mL at {flow_rate_ml_min}mL/min...")
        print(f"Revs per minute...{revs_per_min}")
        
        for _ in range(total_steps):
            self.step.value(1)
            time.sleep_us(delay_us)
            self.step.value(0)
            time.sleep_us(delay_us)
            
        print("Dosing complete.")


if __name__ == "__main__":
    stepper = stepper(stepper={"step_pin": 4, "dir_pin": 2, "enable_pin": 39})
    try:
        stepper.enable.value(0)
        time.sleep_us(200)
        stepper.pump_volume(ml=50.5, flow_rate_ml_min=600.0)
        #stepper.pump_volume(ml=5.5, flow_rate_ml_min=100.0)
        stepper.enable.value(1) 
    except KeyboardInterrupt:
        pass