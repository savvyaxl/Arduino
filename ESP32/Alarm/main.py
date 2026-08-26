
import uasyncio as asyncio # type: ignore
from SmartHomeManager import SmartHomeManager


manager = SmartHomeManager(owPin=None, scl=7, sda=9)
try:
    asyncio.run(manager.run())
except KeyboardInterrupt:
    pass