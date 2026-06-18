# from SmartHomeManager import SmartHomeManager
from wifi_as import WiFiHandler
import time

WiFiHandler("esp32-alarm")
# manager = SmartHomeManager()
time.sleep(2) # Wait for WiFi to connect
# manager.sync_time()