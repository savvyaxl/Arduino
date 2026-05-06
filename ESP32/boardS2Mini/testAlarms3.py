import uasyncio as asyncio # type: ignore
from alex.SmartHomeManager import SmartHomeManager

# --- EXECUTION ---
# Ensure you connect to WiFi first in boot.py or main.py
manager = SmartHomeManager(utc_offset=-3)
try:
    asyncio.run(manager.run())
except KeyboardInterrupt:
    pass
