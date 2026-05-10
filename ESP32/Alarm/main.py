
import uasyncio as asyncio # type: ignore
from SmartHomeManager import SmartHomeManager

manager = SmartHomeManager()
try:
    asyncio.run(manager.run())
except KeyboardInterrupt:
    pass