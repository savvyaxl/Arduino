
from batterytester import BatteryTester


manager = BatteryTester(adc_pin_num=5, mosfet_pin_num=33, r_load=4.7, r1=46800, r2=9740, dutyMax = 1023, DeviceName="Flat 1 Battery Tester")
try:
    manager.run()
except KeyboardInterrupt:
    pass